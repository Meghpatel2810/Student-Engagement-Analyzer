import cv2
import numpy as np
import torch
from ultralytics import YOLO
from collections import deque, defaultdict
import math
import torch.nn as nn
import tempfile
import os

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=50):
        super(PositionalEncoding, self).__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)
    def forward(self, x): return x + self.pe[:x.size(0), :]

class BehaviorTransformer(nn.Module):
    def __init__(self, num_classes, d_model=32, nhead=4, num_encoder_layers=2, dim_feedforward=64, dropout=0.1, seq_len=16):
        super(BehaviorTransformer, self).__init__()
        self.d_model = d_model
        self.input_projection = nn.Linear(num_classes, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len=seq_len)
        encoder_layers = nn.TransformerEncoderLayer(d_model, nhead, dim_feedforward, dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_encoder_layers)
        self.classifier = nn.Linear(d_model, num_classes)
    def forward(self, src):
        src = self.input_projection(src) * math.sqrt(self.d_model)
        src = src.permute(1, 0, 2)
        src = self.pos_encoder(src)
        src = src.permute(1, 0, 2)
        output = self.transformer_encoder(src)
        output = output.mean(dim=1)
        return self.classifier(output)

# Setup paths based on project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YOLO_MODEL_PATH = os.path.join(BASE_DIR, "models", "Nano best.pt")
TRANSFORMER_MODEL_PATH = os.path.join(BASE_DIR, "models", "behavior_transformer.pth")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Global models to avoid reloading on every request
yolo_model = None
transformer_model = None

def load_models():
    global yolo_model, transformer_model
    if yolo_model is None or transformer_model is None:
        yolo_model = YOLO(YOLO_MODEL_PATH)
        transformer_model = BehaviorTransformer(num_classes=8, seq_len=16).to(device)
        transformer_model.load_state_dict(torch.load(TRANSFORMER_MODEL_PATH, map_location=device, weights_only=True))
        transformer_model.eval()

def get_engagement_level(score):
    if score > 1.25: return "V. Engaged" # E4
    if score > 0.5: return "Engaged"    # E3
    if score > -0.5: return "Nominal"    # E2
    return "Not Engaged"              # E1

def process_video(input_path: str, output_path: str):
    load_models()
    
    SEQUENCE_LENGTH = 16
    NUM_CLASSES = 8
    CLASS_NAMES = {0: 'write', 1: 'read', 2: 'lookup', 3: 'turn_head', 4: 'rais_hand', 5: 'stand', 6: 'discuss', 7: 'background'}
    BEHAVIOR_SCORES = {'rais_hand': 2, 'write': 1, 'read': 1, 'lookup': 0, 'stand': 0, 'turn_head': -1, 'discuss': -2, 'background': 0}
    SCORE_HISTORY_LENGTH = 90
    COLOR_MAPPING = {"V. Engaged": (0, 255, 0), "Engaged": (144, 238, 144), "Nominal": (255, 255, 255), "Not Engaged": (0, 0, 255)}

    cap = cv2.VideoCapture(input_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps != fps: fps = 25.0
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    student_histories = defaultdict(lambda: {
        'behavior_history': deque(maxlen=SEQUENCE_LENGTH), 'score_history': deque(maxlen=SCORE_HISTORY_LENGTH),
        'final_behavior': 'lookup', 'avg_score': 0.0, 'bbox': None
    })

    while True:
        success, frame = cap.read()
        if not success: break

        results = yolo_model.track(frame, persist=True, verbose=False, tracker="bytetrack.yaml")
        current_frame_tracks = {}

        try:
            boxes = results[0].boxes.xyxy.cpu()
            if results[0].boxes.id is not None:
                track_ids = results[0].boxes.id.int().cpu().tolist()
                clss = results[0].boxes.cls.int().cpu().tolist()

                for box, track_id, cls_id in zip(boxes, track_ids, clss):
                    if CLASS_NAMES.get(cls_id) == 'background': continue
                    
                    current_frame_tracks[track_id] = {'bbox': box, 'class_id': cls_id}
                    student = student_histories[track_id]
                    student['bbox'] = box 
                    student['behavior_history'].append(cls_id)
                    
                    if len(student['behavior_history']) == SEQUENCE_LENGTH:
                        history = list(student['behavior_history'])
                        one_hot_sequence = np.zeros((1, SEQUENCE_LENGTH, NUM_CLASSES), dtype=np.float32)
                        for i, cid in enumerate(history): one_hot_sequence[0, i, cid] = 1.0
                        
                        with torch.no_grad():
                            output = transformer_model(torch.from_numpy(one_hot_sequence).to(device))
                            student['final_behavior'] = CLASS_NAMES.get(torch.max(output.data, 1)[1].item())
                    
                    current_score = BEHAVIOR_SCORES.get(student['final_behavior'], 0)
                    student['score_history'].append(current_score)
                    student['avg_score'] = np.mean(student['score_history'])
        except Exception:
            pass
            
        for track_id, student_data in student_histories.items():
            if track_id in current_frame_tracks:
                x1, y1, x2, y2 = map(int, student_data['bbox'])
                engagement_level = get_engagement_level(student_data['avg_score'])
                color = COLOR_MAPPING.get(engagement_level, (128, 128, 128))

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"ID:{track_id} | {engagement_level}"
                font_scale = 0.4
                thickness = 1
                
                (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                cv2.rectangle(frame, (x1, y1 - h - 10), (x1 + w, y1), color, -1)
                cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)
            
        video_writer.write(frame)
    
    cap.release()
    video_writer.release()
