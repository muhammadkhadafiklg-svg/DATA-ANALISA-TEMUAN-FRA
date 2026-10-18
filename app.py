# ==========================================
# 7. AI ASISTEN (CHAT - RINGKASAN STATISTIK AKURAT)
# ==========================================
st.markdown("<hr style='margin-top: 40px;'>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#000000; font-weight:800;'>🤖 AI Asisten</h3>", unsafe_allow_html=True)
st.caption("Saya adalah asisten M Khadafi dan siap menjawab pertanyaan tentang data yang ditampilkan.")

if "GROQ_API_KEY" in st.secrets:
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, SystemMessage
        
        llm = ChatGroq(
            groq_api_key=st.secrets["GROQ_API_KEY"], 
            model_name="openai/gpt-oss-20b", 
            temperature=0.1
        )
        
        # Membuat ringkasan data teragregasi per bulan & toko agar aman dari limit token dan sangat akurat
        ringkasan_per_bulan = df_mentah[df_mentah['Ada Temuan'] == True].groupby(['Bulan', 'Tahun', 'NAMA STORE', 'Kategori Temuan', 'DETAIL TEMUAN']).size().reset_index(name='Jumlah')
        data_statistik = ringkasan_per_bulan.to_markdown(index=False)
        
        pertanyaan = st.chat_input("Ketik pertanyaan Anda di sini (Contoh: Bandingkan temuan September dan Oktober 2026)...")
        
        if pertanyaan:
            with st.chat_message("user"):
                st.write(pertanyaan)
            
            with st.chat_message("assistant"):
                with st.spinner('Memproses analisa data...'):
                    
                    system_prompt = (
                        "Anda adalah AI Asisten untuk M Khadafi yang mengelola data analisa operasional toko. "
                        "Berikut adalah data statistik temuan operasional lengkap berdasarkan bulan, toko, dan kategori:\n\n"
                        f"{data_statistik}\n\n"
                        "Tugas Anda: Jawab pertanyaan analitik berdasarkan data tabel tersebut secara cermat. "
                        "Jika pengguna menanyakan perbandingan bulan (seperti September dan Oktober 2026), teliti kolom Bulan dan Kategori/Detail Temuan untuk mencocokkan apakah ada toko atau kasus temuan yang sama atau berulang.\n"
                        "ATURAN MUTLAK:\n"
                        "1. DILARANG menggunakan kata 'bermasalah', 'kritis', atau 'perlu atensi'. \n"
                        "2. Gunakan istilah objektif seperti 'toko dengan temuan', 'frekuensi temuan', atau 'analisa data'. \n"
                        "3. Jawablah menggunakan Bahasa Indonesia yang sangat rapi, analitis, sopan, dan netral."
                    )
                    
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=pertanyaan)
                    ]
                    
                    response = llm.invoke(messages)
                    st.write(response.content)
                    
    except Exception as e:
        st.error(f"Koneksi AI mengalami kendala teknis: {e}")
else:
    st.warning("⚠️ Kunci GROQ_API_KEY belum dikonfigurasi di menu Settings > Secrets Streamlit.")
