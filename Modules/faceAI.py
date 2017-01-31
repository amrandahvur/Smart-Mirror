from selfieAI import SendMail, capture
from speechRecAI import SpeechAI
import sys
import cv2

class faceAI(object):
    def __init__(self,model = "faceModels/facial_recognition_model.xml",camera=0):
        self.recognitionModel = model
        self.source = camera

    def detect_face(self):
        face_cascade = cv2.CascadeClassifier(self.recognitionModel)
        video_capture = cv2.VideoCapture(self.source)

        while True:
            ret, frame = video_capture.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            if len(faces) > 0:
                video_capture.release()
                cv2.destroyAllWindows()

                return True

    def show_live_detection(self):
        face_cascade = cv2.CascadeClassifier(self.recognitionModel)
        video_capture = cv2.VideoCapture(self.source)

        while True:
            ret, frame = video_capture.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        video_capture.release()
        cv2.destroyAllWindows()

    def theft_mode(self):
        F = faceAI()
        S = SpeechAI()
        record,audio = S.ears()
        theftKey = S.recognize(record,audio)
        if "save" in theftKey:
            while True:
                if F.detect_face():
                    capture(True)
                    SendMail('filename.jpg',True)
                    return 1

if __name__ == "__main__":
    F = faceAI()
    F.show_live_detection()
    """
    Comment the above line & 
    Remove Comments below to Enable Theft
    Mode for the Mirror.
    """
    # while True:
    #     if F.theft_mode() == 1:
    #         break
