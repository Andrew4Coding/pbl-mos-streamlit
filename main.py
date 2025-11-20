import streamlit as st
import json
import os
from datetime import datetime
from database import (
    save_participant, 
    save_evaluation,
    get_evaluation_statistics,
    check_participant_exists
)

# Load the dataset
@st.cache_data
def load_dataset():
    with open('final_dataset.json', 'r') as f:
        return json.load(f)

def statistics_page():
    """Display statistics page"""
    st.set_page_config(page_title="Statistik Evaluasi - Lagi Bentar", layout="wide")
    
    st.title("📊 Statistik Evaluasi MOS")
    st.markdown("---")
    
    try:
        stats = get_evaluation_statistics()
        
        st.subheader("📈 Ringkasan Statistik")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Partisipan", stats['total_participants'])
        with col2:
            avg_all = sum([s['average_rating'] for s in stats['model_statistics']]) / len(stats['model_statistics']) if stats['model_statistics'] else 0
            st.metric("Rata-rata Semua Model", f"{avg_all:.2f}")
        
        st.markdown("---")
        st.markdown("### 🎯 Statistik Per Model")
        
        for stat in stats['model_statistics']:
            with st.container():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Model {stat['model_id']}**")
                    st.caption(stat['model_name'])
                with col2:
                    st.metric("Rata-rata Rating", f"{stat['average_rating']:.2f}")
                st.markdown("---")
                
    except Exception as e:
        st.error(f"Error mengambil statistik: {str(e)}")

def main():
    st.set_page_config(page_title="MOS Evaluation Form - Lagi Bentar", layout="wide")
    
    # Title and Introduction
    st.title("🎙️ Mean Opinion Score (MOS) Evaluation Form")
    st.markdown("---")
    
    st.markdown("""
    ### Perkenalkan kami dari kelompok "Lagi Bentar" yang terdiri dari:
    1. **Arya Raditya Kusuma (2306215816)**
    2. **Andrew Devito Aryo (2306152494)**
    
    ---
    
    ### Instruksi Penilaian
    
    Partisipan dimohon memberikan penilaian terkait kualitas audio yang dihasilkan oleh model TTS. 
    
    **⚠️ Penting:** Saat ingin mendengarkan audio, tolong agar membuka link audio di tab baru agar tidak meninggalkan form ini.
    
    ### Model yang Dievaluasi:
    
    **Untuk Dataset Sunda:**
    - **Model A:** FastPitch + HiFi-GAN (pretrained) pada dataset Sunda
    - **Model B:** FastPitch + HiFi-GAN (fine-tuned) pada dataset Sunda
    - **Model C:** VITS (pretrained) pada dataset Sunda
    - **Model D:** VITS (fine-tuned) pada dataset Sunda
    
    **Untuk Dataset Bahasa Indonesia:**
    - **Model E:** VITS (pretrained) pada dataset Bahasa Indonesia
    - **Model F:** VITS (fine-tuned) pada dataset Bahasa Indonesia
    
    ---
    
    ### Skala Penilaian (1-5):
    - **5 - Excellent:** Kualitas sangat baik, sangat natural
    - **4 - Good:** Kualitas baik, cukup natural
    - **3 - Fair:** Kualitas cukup, sedikit tidak natural
    - **2 - Poor:** Kualitas kurang, tidak natural
    - **1 - Bad:** Kualitas sangat buruk, sangat tidak natural
    """)
    
    st.markdown("---")
    
    # Load dataset
    dataset = load_dataset()
    sunda_samples = [s for s in dataset if s['type'] == 'sunda']
    indonesian_samples = [s for s in dataset if s['type'] == 'indonesian']
    
    # Participant Information
    st.header("📝 Informasi Partisipan")
    participant_name = st.text_input("Nama Lengkap:", key="participant_name")
    participant_email = st.text_input("Email:", key="participant_email")
    
    st.markdown("---")
    
    # Initialize session state for responses
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    
    # SUNDA SECTIONS
    st.header("🔊 Evaluasi Dataset Sunda")
    st.markdown("Silakan dengarkan audio original dan audio dari setiap model, lalu berikan penilaian kualitas untuk masing-masing model.")
    
    for idx, sample in enumerate(sunda_samples):
        st.markdown("---")
        st.subheader(f"📁 Sampel Sunda #{idx + 1}")
        st.markdown(f"**File:** `{sample['original_audio']}`")
        
        # Original Audio and Text
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("**🎵 Audio Original:**")
            if os.path.exists(sample['original_audio']):
                st.audio(sample['original_audio'])
            else:
                st.warning("File audio tidak ditemukan")
        
        with col2:
            st.markdown("**📝 Transkrip Original:**")
            st.info(sample['original_text'])
        
        st.markdown("#### Evaluasi Model")
        
        # Create 4 columns for 4 models
        cols = st.columns(4)
        
        models = [
            ('A', 'FastPitch+HiFi-GAN (Pretrained)', sample['pretrained_fastpitch_audio']),
            ('B', 'FastPitch+HiFi-GAN (Fine-tuned)', sample['finetuned_fastpitch_audio']),
            ('C', 'VITS (Pretrained)', sample['pretrained_vits']),
            ('D', 'VITS (Fine-tuned)', sample['finetuned_vits'])
        ]
        
        for col_idx, (model_id, model_name, audio_path) in enumerate(models):
            with cols[col_idx]:
                st.markdown(f"**Model {model_id}**")
                st.caption(model_name)
                if audio_path and os.path.exists(audio_path):
                    st.audio(audio_path)
                else:
                    st.warning("Audio tidak tersedia")
                
                # Rating
                rating_key = f"sunda_{idx}_model_{model_id}"
                rating = st.radio(
                    f"Penilaian Model {model_id}:",
                    options=[5, 4, 3, 2, 1],
                    format_func=lambda x: f"{x} - {'Excellent' if x==5 else 'Good' if x==4 else 'Fair' if x==3 else 'Poor' if x==2 else 'Bad'}",
                    key=rating_key,
                    horizontal=False
                )
                st.session_state.responses[rating_key] = rating
    
    # INDONESIAN SECTIONS
    st.markdown("---")
    st.header("🔊 Evaluasi Dataset Bahasa Indonesia")
    st.markdown("Silakan dengarkan audio original dan audio dari setiap model, lalu berikan penilaian kualitas untuk masing-masing model.")
    
    for idx, sample in enumerate(indonesian_samples):
        st.markdown("---")
        st.subheader(f"📁 Sampel Indonesia #{idx + 1}")
        st.markdown(f"**File:** `{sample['original_audio']}`")
        
        # Original Audio and Text
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("**🎵 Audio Original:**")
            if os.path.exists(sample['original_audio']):
                st.audio(sample['original_audio'])
            else:
                st.warning("File audio tidak ditemukan")
        
        with col2:
            st.markdown("**📝 Transkrip Original:**")
            st.info(sample['original_text'])
        
        st.markdown("#### Evaluasi Model")
        
        # Create 2 columns for 2 models
        cols = st.columns(2)
        
        models = [
            ('E', 'VITS (Pretrained)', sample['pretrained_vits']),
            ('F', 'VITS (Fine-tuned)', sample['finetuned_vits'])
        ]
        
        for col_idx, (model_id, model_name, audio_path) in enumerate(models):
            with cols[col_idx]:
                st.markdown(f"**Model {model_id}**")
                st.caption(model_name)
                if audio_path and os.path.exists(audio_path):
                    st.audio(audio_path)
                else:
                    st.warning("Audio tidak tersedia")
                
                # Rating
                rating_key = f"indonesian_{idx}_model_{model_id}"
                rating = st.radio(
                    f"Penilaian Model {model_id}:",
                    options=[5, 4, 3, 2, 1],
                    format_func=lambda x: f"{x} - {'Excellent' if x==5 else 'Good' if x==4 else 'Fair' if x==3 else 'Poor' if x==2 else 'Bad'}",
                    key=rating_key,
                    horizontal=False
                )
                st.session_state.responses[rating_key] = rating
    
    # Submit Button
    st.markdown("---")
    st.header("✅ Submit Evaluasi")
    
    if st.button("📤 Submit Evaluasi", type="primary", use_container_width=True):
        if not participant_name or not participant_email:
            st.error("⚠️ Mohon isi Nama dan Email sebelum submit!")
        else:
            try:
                # Check if participant already submitted
                existing = check_participant_exists(participant_email)
                if existing:
                    st.warning(f"⚠️ Email {participant_email} sudah pernah melakukan evaluasi sebelumnya.")
                    if not st.checkbox("Saya ingin submit evaluasi baru", key="override_submit"):
                        st.stop()
                
                # Save participant to database
                participant_id = save_participant(participant_name, participant_email)
                
                # Save all evaluations to database
                evaluation_count = 0
                
                # Process Sunda evaluations
                for idx, sample in enumerate(sunda_samples):
                    models = [
                        ('A', 'FastPitch+HiFi-GAN (Pretrained)', sample['pretrained_fastpitch_audio']),
                        ('B', 'FastPitch+HiFi-GAN (Fine-tuned)', sample['finetuned_fastpitch_audio']),
                        ('C', 'VITS (Pretrained)', sample['pretrained_vits']),
                        ('D', 'VITS (Fine-tuned)', sample['finetuned_vits'])
                    ]
                    
                    for model_id, model_name, audio_path in models:
                        rating_key = f"sunda_{idx}_model_{model_id}"
                        if rating_key in st.session_state.responses:
                            rating = st.session_state.responses[rating_key]
                            save_evaluation(
                                participant_id=participant_id,
                                sample_type='sunda',
                                sample_index=idx,
                                model_id=model_id,
                                model_name=model_name,
                                rating=rating,
                                audio_path=audio_path,
                                original_text=sample['original_text']
                            )
                            evaluation_count += 1
                
                # Process Indonesian evaluations
                for idx, sample in enumerate(indonesian_samples):
                    models = [
                        ('E', 'VITS (Pretrained)', sample['pretrained_vits']),
                        ('F', 'VITS (Fine-tuned)', sample['finetuned_vits'])
                    ]
                    
                    for model_id, model_name, audio_path in models:
                        rating_key = f"indonesian_{idx}_model_{model_id}"
                        if rating_key in st.session_state.responses:
                            rating = st.session_state.responses[rating_key]
                            save_evaluation(
                                participant_id=participant_id,
                                sample_type='indonesian',
                                sample_index=idx,
                                model_id=model_id,
                                model_name=model_name,
                                rating=rating,
                                audio_path=audio_path,
                                original_text=sample['original_text']
                            )
                            evaluation_count += 1
                
                # Also save to JSON file as backup
                submission = {
                    'timestamp': datetime.now().isoformat(),
                    'participant_id': participant_id,
                    'participant_name': participant_name,
                    'participant_email': participant_email,
                    'responses': st.session_state.responses
                }
                
                submission_file = f'submissions/submission_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{participant_name.replace(" ", "_")}.json'
                os.makedirs('submissions', exist_ok=True)
                
                with open(submission_file, 'w') as f:
                    json.dump(submission, f, indent=2)
                
                # Success messages
                st.success(f"✅ Terima kasih {participant_name}! Evaluasi Anda telah berhasil disimpan ke database.")
                st.info(f"📊 Total {evaluation_count} evaluasi tersimpan (Participant ID: {participant_id})")
                
                # Additional confirmation message
                st.markdown("""
                ### 🎉 Submission Berhasil!
                
                Data evaluasi Anda telah tersimpan dengan aman. Berikut rinciannya:
                - **Nama:** {name}
                - **Email:** {email}
                - **Total Evaluasi:** {count} penilaian
                - **Waktu Submit:** {time}
                
                Terima kasih atas partisipasi Anda dalam penelitian ini! 🙏
                """.format(
                    name=participant_name,
                    email=participant_email,
                    count=evaluation_count,
                    time=datetime.now().strftime("%d %B %Y, %H:%M:%S")
                ))
                
                st.balloons()
                
                # Show summary
                with st.expander("📊 Lihat Ringkasan Penilaian Anda"):
                    st.json(submission)
                    
            except Exception as e:
                st.error(f"❌ Error saat menyimpan evaluasi: {str(e)}")
                st.info("Data tetap tersimpan sebagai backup file di folder 'submissions'")

if __name__ == "__main__":
    main()
