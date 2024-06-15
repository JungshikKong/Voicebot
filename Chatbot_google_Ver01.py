import streamlit as st
from audiorecorder import audiorecorder
import openai
import os
from datetime import datetime
from gtts import gTTS
import base64
import speech_recognition as sr
import logging
import pyttsx3 as p

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)

##### Google STT 관련 함수 #####
def google_STT_with_File(audio_File):
    r = sr.Recognizer()
    with sr.AudioFile(audio_File) as source:
        audio = r.record(source)  # 전체 audio file 읽기
    text = []
    try:
        print("Google Speech Recognition thinks you said : " + r.recognize_google(audio, language='ko'))
        text = [r.recognize_google(audio, language='ko')]
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
    return text

def google_STT_no_File():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something!")
        audio = r.listen(source)
    text = []
    try:
        print("Google Speech Recognition thinks you said : " + r.recognize_google(audio, language='ko'))
        text = [r.recognize_google(audio, language='ko')]
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
    return text

##### 기능 구현 함수 #####
def STT(audio):
    filename = 'input.wav'
    audio.export(filename, format="wav")
    audio_file = open(filename, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    audio_file.close()
    os.remove(filename)
    return transcript["text"]

def ask_gpt(prompt, model, apikey):
    client = openai.OpenAI(api_key=apikey)
    try:
        response = client.chat.completions.create(model=model, messages=prompt)
        system_message = response.choices[0].message['content']
        
        return system_message
    
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        return {"error": str(e)}
    except Exception as e:
        logging.error(f"General error: {e}")
        return {"error": str(e)}

def TTS_google(response):
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    os.remove(filename)

def TTS_pyttsx3(response):
    e = p.init()
    e.say(response)
    e.runAndWait()
    

def main():
    st.set_page_config(
        page_title="내품당 음성 비서",
        layout="wide"
    )
    
    def play_intro():
        intro = "안녕하세요 비서 내품입니다. 무엇을 도와드릴까요?"
        TTS_google(intro)
    
   # Intro 소리를 한 번만 재생하기 위해 세션 상태 확인 및 설정
    # Intro 소리를 한 번만 재생하기 위해 세션 상태 확인 및 설정
    if "played_intro" not in st.session_state:
        st.session_state["played_intro"] = False

    if not st.session_state["played_intro"]:
        st.session_state["played_intro"] = True
        play_intro()

    if "OPENAI_API" not in st.session_state:
        st.session_state["OPENAI_API"] = ""
        
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in Korean"}]

    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False

    st.header("내품당 음성 비서")
    st.markdown("---")

    with st.expander("내품당 음성 비서에 관하여", expanded=True):
        st.write("""
        - 당뇨인 커뮤니티 3.0 내품당은.
        - 질병 중심이 아닌 삶
        - 새로운 전환, 압도적인 지배를 통해
        - 당신의 삶을 재정의 하고 주도권을 쥐고 결정할 수 있도록 돕겠습니다.
        """)
        st.markdown("")
       
    with st.sidebar:
        st.session_state["OPENAI_API"] = st.text_input( label="OPENAI API 키",
                                                        placeholder="Enter Your API Key",
                                                        value="",
                                                        type="password")

        st.markdown("---")
        model = st.radio(label="GPT 모델", options=["gpt-4", "gpt-3.5-turbo"], index=1)

        st.markdown("---")

        if st.button(label="초기화"):
            st.session_state["played_intro"] = False
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role": "system", "content":  "You are a thoughtful assistant. Respond to all input in 25 words and answer in Korean"}]
            st.session_state["check_reset"] = True

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("질문하기")
        audio = audiorecorder("클릭하여 녹음하기", "녹음중...")
        if (audio.duration_seconds > 0) and (not st.session_state["check_reset"]):
            #음성 재생
            st.audio(audio.export().read())
            
            #음원 파일에서 텍스트 추출
            filename = 'input.wav'
            audio.export(filename, format="wav")
            question = google_STT_with_File(filename)
            
            #채팅을 시각화하기 위해 질문 내용 저장
            now = datetime.now().strftime("%H:%M")
            #st.session_state["chat"] = st.session_state["chat"] + [("user", now, ' '.join(question))]
            st.session_state["chat"] = [("user", now, ' '.join(question))]
            
            #GPT 모델에 넢을 프롬프트를 위해 질문 내용 저장
            st.session_state["messages"] = [{"role": "system", "content":  "You are a thoughtful assistant. Respond to all input in 25 words and answer in Korean"}]
            st.session_state["messages"] = st.session_state["messages"]+[{"role": "user", "content": ' '.join(question)}]
            
            #질문 내용 확인
            print(st.session_state["messages"])

    with col2:
        st.subheader("질문/답변")
        if (audio.duration_seconds > 0) and (not st.session_state["check_reset"]):
            # ChatGPT에게 답변 얻기
            client = openai.OpenAI(api_key=st.session_state["OPENAI_API"])
            model = "gpt-3.5-turbo"
            response = client.chat.completions.create(model=model, messages=st.session_state["messages"])
            
            # GPT 모델에 넣을 프롬프트를 위해 답변 내용 저장
            #st.session_state["message"] = st.session_state["messages"]+[{"role":"system","content":' '.join(response.choices[0].message.content)}]
            
            #채팅 시각화를 위한 답변 내용 저장
            now = datetime.now().strftime("%H:%M")
            receivced_message = ' '.join(response.choices[0].message.content)
            st.session_state["chat"] = st.session_state["chat"]+[("bot", now, receivced_message)]
            
            #채팅 형식으로 시각화하기
            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("")
                else:
                    st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("")

             # 음성으로 읽어주기
            TTS_google(receivced_message)
        else:
            st.session_state["check_reset"] = False

if __name__ == "__main__":
    main()


