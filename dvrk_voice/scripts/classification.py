from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import pickle

class Classification:
    def __init__(self):
        pass

    def sort(self, command):
        #load the model and tokenizer
        model_path = "./data/sort_distilroberta-base"
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        #load the label encoder
        with open(f"{model_path}/label_encoder.pkl", "rb") as f:
            label_encoder = pickle.load(f)
        id2label = dict(enumerate(label_encoder.classes_))
        #create the classifier pipeline
        classifier = pipeline("text-classification", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)
        #classify the command
        prompt = command
        result = classifier(prompt, top_k=1)[0]
        label_id = int(result['label'].split("_")[-1]) if result['label'].startswith("LABEL_") else int(result['label'])
        predicted_label = id2label[label_id]
        #print the predicted label
        print(predicted_label)
        return predicted_label

    def tools(self,command):
        #load the model and tokenizer
        model_path = "./data/tools_distilroberta-base"
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        #load the label encoder
        with open(f"{model_path}/label_encoder.pkl", "rb") as f:
            label_encoder = pickle.load(f)
        id2label = dict(enumerate(label_encoder.classes_))
        #create the classifier pipeline
        classifier = pipeline("text-classification", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)
        #classify the command
        prompt = command
        result = classifier(prompt, top_k=1)[0]
        label_id = int(result['label'].split("_")[-1]) if result['label'].startswith("LABEL_") else int(result['label'])
        predicted_label = id2label[label_id]
        #print the predicted label
        print(predicted_label)
        return predicted_label

    def start_stop(self, command):
        #load the model and tokenizer
        model_path = "./data/start_stop_distilroberta-base"
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        #load the label encoder
        with open(f"{model_path}/label_encoder.pkl", "rb") as f:
            label_encoder = pickle.load(f)
        id2label = dict(enumerate(label_encoder.classes_))
        #create the classifier pipeline
        classifier = pipeline("text-classification", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)
        #classify the command
        prompt = command
        result = classifier(prompt, top_k=1)[0]
        label_id = int(result['label'].split("_")[-1]) if result['label'].startswith("LABEL_") else int(result['label'])
        predicted_label = id2label[label_id]
        #print the predicted label
        print(predicted_label)
        return predicted_label

    def camera(self,command):
        #load the model and tokenizer
        model_path = "./data/camera_distilroberta-base"
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        #load the label encoder
        with open(f"{model_path}/label_encoder.pkl", "rb") as f:
            label_encoder = pickle.load(f)
        id2label = dict(enumerate(label_encoder.classes_))
        #create the classifier pipeline
        classifier = pipeline("text-classification", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)
        #classify the command
        prompt = command
        result = classifier(prompt, top_k=1)[0]
        label_id = int(result['label'].split("_")[-1]) if result['label'].startswith("LABEL_") else int(result['label'])
        predicted_label = id2label[label_id]
        #print the predicted label
        print(predicted_label)
        return predicted_label

    def draw(self,command):
        #load the model and tokenizer
        model_path = "./data/draw_distilroberta-base"
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        #load the label encoder
        with open(f"{model_path}/label_encoder.pkl", "rb") as f:
            label_encoder = pickle.load(f)
        id2label = dict(enumerate(label_encoder.classes_))
        #create the classifier pipeline
        classifier = pipeline("text-classification", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)
        #classify the command
        prompt = command
        result = classifier(prompt, top_k=1)[0]
        label_id = int(result['label'].split("_")[-1]) if result['label'].startswith("LABEL_") else int(result['label'])
        predicted_label = id2label[label_id]
        #print the predicted label
        print(predicted_label)
        return predicted_label

    def patient(self,command):
        #load the model and tokenizer
        model_path = "./data/patient_distilroberta-base"
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        #load the label encoder
        with open(f"{model_path}/label_encoder.pkl", "rb") as f:
            label_encoder = pickle.load(f)
        id2label = dict(enumerate(label_encoder.classes_))
        #create the classifier pipeline
        classifier = pipeline("text-classification", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)
        #classify the command
        prompt = command
        result = classifier(prompt, top_k=1)[0]
        label_id = int(result['label'].split("_")[-1]) if result['label'].startswith("LABEL_") else int(result['label'])
        predicted_label = id2label[label_id]
        #print the predicted label
        print(predicted_label)
        return predicted_label

    def handle_command(self, command):
        category = self.sort(command)
        if category == "tools":
            self.tools(command)
        elif category == "start_stop":
            self.start_stop(command)
        elif category == "camera":
            self.camera(command)
        elif category == "draw":
            self.draw(command)
        elif category == "patient":
            self.patient(command)
        elif category == "NV":
            return category
        else:
            print("Impossible to classify the command. Sorry...")
            return None