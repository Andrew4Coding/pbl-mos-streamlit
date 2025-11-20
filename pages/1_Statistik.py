import streamlit as st
from database import get_evaluation_statistics, get_all_participants
import pandas as pd

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
    
    # Display participants list
    st.markdown("---")
    st.subheader("👥 Daftar Partisipan")
    
    participants = get_all_participants()
    
    if participants:
        # Convert to DataFrame for better display
        df = pd.DataFrame(participants)
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%d %B %Y, %H:%M:%S')
        df = df.rename(columns={
            'id': 'ID',
            'name': 'Nama',
            'email': 'Email',
            'created_at': 'Waktu Submit',
            'total_evaluations': 'Total Evaluasi'
        })
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        st.info(f"📊 Total: {len(participants)} partisipan telah mengisi form evaluasi")
    else:
        st.info("Belum ada partisipan yang mengisi form evaluasi.")
            
except Exception as e:
    st.error(f"Error mengambil statistik: {str(e)}")
