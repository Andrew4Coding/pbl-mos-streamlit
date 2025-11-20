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
        if stats['model_statistics']:
            avg_all = sum([float(s['average_rating']) for s in stats['model_statistics']]) / len(stats['model_statistics'])
            st.metric("Rata-rata Semua Model", f"{avg_all:.2f}")
        else:
            st.metric("Rata-rata Semua Model", "0.00")
    
    st.markdown("---")
    st.markdown("### 🎯 Statistik Per Model")
    
    if stats['model_statistics']:
        for stat in stats['model_statistics']:
            with st.container():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Model {stat['model_id']}**")
                    st.caption(stat['model_name'])
                with col2:
                    st.metric("Rata-rata Rating", f"{float(stat['average_rating']):.2f}")
                st.markdown("---")
    else:
        st.info("Belum ada data evaluasi untuk ditampilkan.")
    
    # Display participants list
    st.markdown("---")
    st.subheader("👥 Daftar Partisipan")
    
    participants = get_all_participants()
    
    if participants:
        # Convert to DataFrame for better display
        df = pd.DataFrame(participants)
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%d %B %Y, %H:%M:%S')
        
        # Sensor participant names (show first and last letter, mask the rest)
        def sensor_name(name):
            if len(name) <= 2:
                return name[0] + '*' * (len(name) - 1)
            return name[0] + '*' * (len(name) - 2) + name[-1]
        
        df['name'] = df['name'].apply(sensor_name)
        
        # Drop email column and rename others
        df = df.drop('email', axis=1).drop('id', axis=1)
        df = df.rename(columns={
            'id': 'ID',
            'name': 'Nama',
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
