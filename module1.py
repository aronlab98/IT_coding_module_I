import speech_recognition
import pyttsx3
import sounddevice
import nltk

nltk.download("punkt")

from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import cv2

import threading
import queue

# global variable(s):
CLOSE = False


# ---------------------------
# SPEECH CHECK
def check_speech_camera(txt):

    # this  function checks everything has been said:
    # IF a couple of words match with 'aprire' and 'fotocamera' or their derivatives,
    # it will return a signal which is going to allow to open the webcam

    stemmer = PorterStemmer()
    open_webc = [stemmer.stem("fotocamera"), stemmer.stem("aprire")]
    words = word_tokenize(txt)

    # check each word in the text and check if it matches any of the root stems
    matches = []
    for word in words:
        if stemmer.stem(word) in open_webc:
            matches.append(word)

    if matches:
        return True
    else:
        return False


def check_speech(txt):

    # this is the function used while the camera is still opened
    # basically it does the same thing as check_speech_camera,
    # but it is used within the thread
    # it checks everything has been said:
    # IF a couple of words match with 'chiudere' and 'fotocamera' or their derivatives,
    # it will return a signal which is going to allow to close the webcam

    global CLOSE

    stemmer = PorterStemmer()
    words = word_tokenize(txt)

    close_webc = [stemmer.stem("fotocamera"), stemmer.stem("chiudere")]
    cw = [word for word in words if stemmer.stem(word) in close_webc]

    if cw:
        CLOSE = True
    else:
        pass


def open_camera():

    # this function takes care about opening the camera

    global CLOSE
    # initialize the camera
    cap = cv2.VideoCapture(0)

    try:
        # check if the webcam is opened correctly
        if not cap.isOpened():
            raise IOError("can't open webcam")

        while True:
            ret, frame = cap.read()
            # if frame is read correctly ret is True
            if not ret:
                print("exiting")
                break

            # display the resulting frame
            cv2.imshow('Webcam', frame)

            # the loop is broken when CLOSE is true, so when 'chiudere' and 'fotocamera'
            # have been said in the same sentence
            # ...the loop is broken even when 'q' is pressed, just in case
            if (cv2.waitKey(1) & 0xFF == ord('q')) or CLOSE:
                break

    except Exception as e:
        print(e)
    finally:
        # at the end release the capture when the loop is broken
        cap.release()
        cv2.destroyAllWindows()


def audio_thread(q):
    global CLOSE
    while True:
        try:
            with speech_recognition.Microphone() as mic:
                recognizer.adjust_for_ambient_noise(mic)  # to 'filter' the sound
                audio = recognizer.listen(mic)  # microphone is listening
                text = recognizer.recognize_google(audio_data=audio, language="it-IT")  # recognize speech
                text = text.lower()
                print(f"recognized: {text}")
                q.put(text)
                check_speech(text)
        except speech_recognition.UnknownValueError:
            print("couldn't understand audio")
        except speech_recognition.RequestError as e:
            print("ERROR service; {0}".format(e))

        if CLOSE:
            return


def main():
    while True:
        try:
            with speech_recognition.Microphone() as mic:
                recognizer.adjust_for_ambient_noise(mic)  # to 'filter' the sound
                audio = recognizer.listen(mic)  # microphone is listening
                text = recognizer.recognize_google(audio_data=audio, language="it-IT")  # recognize speech
                text = text.lower()
                print(f"recognized: {text}")
                bln = check_speech_camera(text)

            if bln:  # if the signal to open the camera is true
                # now, a thread is going to be initialized
                # in this way it is possible to have the camera opened *and*
                # listening to what the person is saying
                audio_q = queue.Queue()
                t = threading.Thread(target=audio_thread, args=(audio_q,))
                t.daemon = True
                t.start()
                open_camera()
            else:
                continue

        except speech_recognition.UnknownValueError:
            print("couldn't understand audio")
            continue

        if CLOSE:
            return


if __name__ == "__main__":
    recognizer = speech_recognition.Recognizer()
    main()
