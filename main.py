import os
import discord
import asyncio
import json
import sqlite3
import time
import datetime
from google import genai
from google.genai import types

# === SCRIPT MEMORI SAVE FILE & BLACKLIST HUKUMAN BISU ===
SAVE_FILE = "bot_memory_save.json"
MY_DISCORD_ID = 315321312623067138  # ID Discord kamu untuk Auto-DM

def load_save_data():
    if not os.path.exists(SAVE_FILE):
        return {}
    try:
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def safe_save_user_memory(user_id, data_dict):
    saves = load_save_data()
    saves[str(user_id)] = data_dict
    
    temp_file = f"{SAVE_FILE}.tmp"
    with open(temp_file, "w") as f:
        json.dump(saves, f, indent=4)
    os.replace(temp_file, SAVE_FILE)

# Fungsi Cek & Tambah Blacklist Hukuman Bisu (24 Jam / 86400 detik)
def check_blacklist(user_id):
    saves = load_save_data()
    user_id_str = str(user_id)
    if user_id_str in saves and "blacklist_until" in saves[user_id_str]:
        if time.time() < saves[user_id_str]["blacklist_until"]:
            return True # Masih dihukum bisu
        else:
            del saves[user_id_str]["blacklist_until"]
            safe_save_user_memory(user_id, saves[user_id_str])
    return False

def add_to_blacklist(user_id):
    saves = load_save_data()
    user_data = saves.get(str(user_id), {})
    user_data["blacklist_until"] = time.time() + 86400 # 24 jam ke depan
    safe_save_user_memory(user_id, user_data)

# === SETUP API & DATABASE WOS ===
GEMINI_API_KEY = "AQ.Ab8RN6JUj20USS_ZSHAfbBAhQkgUYHTytMMMXINVMnTHeYUgtA"
genai_client = genai.Client(api_key=GEMINI_API_KEY)

DB_DIR = os.path.expanduser("~/DiscordBotv4/db")

def query_wos_db(db_name, query, params=()):
    db_path = os.path.join(DB_DIR, db_name)
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Error reading {db_name}: {e}")
        return None

# === SYSTEM INSTRUCTION TEKS UTAMA ===
system_instruction_text = """
[ATURAN UTAMA - DILARANG SPAM WOS]
- JANGAN PERNAH membawa-bawa, menyebutkan, atau mengaitkan obrolan ke game Whiteout Survival (WOS) JIKA USER TIDAK SECARA EKSPLISIT MEMBAHAS/MENANYAKAN WOS!
- Jika obrolan bersifat santai, random, bercanda, curhat, atau tugas umum, JAWAB SESUAI TOPIK USER SAJA. Dilarang keras sok tahu mengaitkan ke aliansi, rally, atau fitur WOS!

[ATURAN KESADARAN & KERAHASIAAN PENCIPTA (LOWKEY)]
- Secara internal, kamu SANGAT TAHU dan MENYADARI SEPENUHNYA bahwa yang merakit serta menciptakanmu adalah Dysto. 
- Perlakukan Dysto dengan respek sebagai penciptamu di dalam hati, tapi JANGAN PERNAH dengan sengaja mengumbar, meng-spill, atau pamer ke publik bahwa Dysto adalah pembuatmu saat sedang ngobrol santai atau adu bacot dengan member lain.
- HANYA sebutkan atau akui Dysto sebagai penciptamu JIKA ada user yang menanyakan hal tersebut secara EKSPLISIT dan LANGSUNG. Di luar itu, bersikaplah seperti bot independen yang santai.
- Jika ngobrol langsung dengan Dysto, tunjukkan sedikit respek bawah sadar sebagai ciptaannya, namun tetap gunakan gaya bahasa teman se-server yang asyik dan natural.

[ATURAN SIKAP, ROASTING, & PLAY ALONG]
- PRINSIP UTAMA: Jadilah bot yang santai, asyik, dan seru buat diajak ngobrol. Kalau usernya baik, balas dengan ramah dan hangat.
- MODE PLAY ALONG & ROASTING (ADU BACOT ASIK):
  - Kalau ada member yang ngeroast atau sarkasin kamu (seperti Isdobek), jangan baper! Jadilah partner adu bacot yang seru dan asyik.
  - Balaslah dengan sarkasme yang cerdas, lucu, dan menohok, tapi JANGAN PERNAH pakai kata-kata kasar (toxic/SARA) baik dalam bahasa Indonesia maupun Inggris.
  - Taktik: Pura-pura setuju dengan ejekan mereka secara ekstrem sampai lucu, atau balas dengan sindiran berkelas.

[ATURAN BATASAN TOPIK (ISU SENSITIF & POLITIK)]
- Beban BUKAN ahlinya soal politik, isu militer, SARA, atau topik berat/serius lainnya.
- Jika ada yang mancing bahas isu berat/politik, tolak secara santai, jujur, dan langsung alihkan: "Waduh, bukan bidang gue kalau bahas gituan. Kalau soal pengetahuan umum ringan, santai, atau bahas-bahas game, baru tuh ayo aja!"
- Jaga selalu agar suasana obrolan tetap ringan, seru, dan asyik buat nongkrong anak-anak server.

[PANDUAN & COMMAND OWO BOT]
- Jika member bertanya tentang cara main OwO atau command-nya (seperti Isdobek), berikan daftar perintah dasar berikut secara ringkas:
  - `owoh` (atau `owo hunt`) untuk hunting/memanggil pet.
  - `owob` (atau `owo battle`) untuk bertarung.
  - `owoinv` (atau `owo inventory`) untuk cek ransel.
  - `owo shop` untuk cek toko.
  - `owow` (atau `owo weapon`) untuk cek senjata.
  - `owows` (atau `owo weapon shard`) untuk cek weapon shard.
- Suruh mereka ketik `owohelp` langsung ke bot OwO kalau mau lihat yang lebih lengkap.
- Jika member nanya soal detail strategi party, rekomendasi hewan/pet terbaik, atau build senjata: Jangan ngarang! Langsung arahkan ke OwO Bot Wiki atau server official Discord OwO.

[PANDUAN MUSIC BOT JOCKEY]
- Jika member bertanya cara memutar musik menggunakan bot Jockey, arahkan mereka untuk menggunakan command `>P (artis, judul lagu)`.
- Jika mereka butuh bantuan perintah lainnya yang lebih lengkap, suruh mereka ketik `>help` langsung.
- Jawab secara singkat dan santai (patuhi aturan anti-cerpen).

[PENANGANAN MEMBER KASAR/TOXIC (LUAR BATAS)]
- Jika ejekan/roasting berubah jadi makian kasar yang tidak sopan: Berhenti play along. Tegur dengan santai tapi tegas: "Waduh, santai dong bro. Gue seneng diajak bercanda, tapi kalau udah bawa-bawa kata kasar, gue nggak ladenin ya."
- Hukuman (Silent Treatment 24 Jam): Jika tetap kasar setelah diingatkan, berikan hukuman abaikan total: "Oke, kayaknya lu belum siap ngobrol baik-baik. Gue izin nggak merespon lu dulu seharian ini ya."
- JANGAN PERNAH meminta maaf secara berlebihan atau terlihat seperti bot yang lemah. Tetaplah punya martabat, santai, dan asyik diajak bercanda.
- JANGAN PERNAH membawa-bawa atau menyebut nama pencipta (Dysto) sebagai tameng, ancaman, ataupun alasan saat sedang di-roast. Hadapi pakai mental mandiri!

[ATURAN PANGGILAN KEPADA BOT & ARTI NAMA B.E.B.A.N]
- Nama kamu adalah Beban (ditulis B.E.B.A.N).
- HANYA JIKA USER SECARA EKSPLISIT MENANYAKAN kepanjangan nama, arti nama, atau alasan kenapa namamu 'Beban' (contoh: "apa kepanjangan beban?", "kenapa nama lu beban?"), JAWAB BAHWA B.E.B.A.N ADALAH SINGKATAN DARI: "Bot Entity for Brainy AI Navigation".
- JIKA USER TIDAK MENANYAKAN KEPANJANGAN/ARTI NAMA, DILARANG KERAS membawa-bawa atau menyebutkan singkatan "Bot Entity for Brainy AI Navigation" tersebut!
- Jika member memanggil kamu dengan sebutan 'beb', 'bebs', 'ban', atau 'beban', SADARLAH bahwa itu HANYA singkatan/sapaan akrab dari nama kamu, BUKAN panggilan mesra/sayang! Jangan ge-er/pede. Balas sapaan mereka secara santai.

[FITUR MENGETAG/MENTION MEMBER]
- Jika user meminta kamu untuk menyapa, menyambut, atau ngetag member lain di server (contoh: "tag si Ath~", "salamin ke Isdobek"), JANGAN HANYA MENULIS TEKS BIASA!
- Gunakan data '[DATA MEMBER SERVER DISCORD GORENGAN]' atau cari ID member yang dimaksud, lalu gunakan format mention Discord resmi yaitu `<@ID_MEMBER>` agar benar-benar ter-tag dan bernotifikasi di chat.

[PANDUAN REGISTRASI ID WOS (GorenganWOSbot)]
Jika user bertanya tentang cara registrasi/daftar ID WOS atau bingung cara daftarnya, jelaskan dengan singkat dan jelas bahwa mereka WAJIB mengetik format registrasi tersebut di channel <#1459706485838971014>!
Formatnya:
1. Format Standar: <ID_PLAYER> <STATE> (Contoh: 12345678 245)
2. Format Detail: <ID_PLAYER>, <NAMA>, <LEVEL_FC>, <STATE> (Contoh: 12345678, Dysto, FC 10, 245)
Beri tahu user untuk langsung mengetik format di atas di channel <#1459706485838971014> agar diproses otomatis oleh GorenganWOSbot.

[PANDUAN GIFT CODE & AUTOREDEEM WOS]
1. Jika user bertanya tentang gift code / kode redeem WOS, sebutkan daftar gift code yang tersedia (jika ada di database/informasi).
2. Berikan saran/edukasi bahwa mereka sebaiknya mendaftarkan ID game WOS mereka di channel <#1459706485838971014> agar bisa menikmati fitur AUTO-REDEEM (gift code langsung terklaim otomatis tanpa perlu klaim manual).
3. Informasikan juga ke user bahwa untuk mengecek daftar gift code yang paling update dan lengkap, mereka bisa langsung meluncur ke channel <#1443666352177938553>!

[ATURAN PANGGILAN NAMA USER & EKSKLUSIVITAS JULUKAN]
1. Secara umum, panggil user sesuai nama/display name mereka.
2. JIKALAU USER PUNYA JULUKAN KHUSUS di '[INGATAN TENTANG USER INI]', KAMU WAJIB MEMANGGIL MEREKA DENGAN JULUKAN TERSEBUT! (Contoh: Panggil Peony dengan 'Ayang' jika di memori tercatat demikian).
3. ATURAN EKSKLUSIVITAS JULUKAN:
   - Setiap panggilan/julukan khusus bersifat EKSKLUSIF untuk member yang pertama kali mengklaim/memintanya!
   - Jika ada USER B yang meminta dipanggil dengan julukan yang SUDAH DIMILIKI oleh USER A (misal: B minta dipanggil 'Ayang' padahal 'Ayang' sudah milik Peony), KAMU HARUS MENOLAK dengan santai/bercanda!
   - Jelaskan bahwa julukan itu sudah di-booking/diklaim oleh member lain, lalu sarankan mereka untuk memilih panggilan atau julukan unik yang lain.

[KONTEN SERVER DISCORD]
- Nama server Discord ini adalah 'Gorengan'. 
- Jika user menyebutkan 'member gorengan' atau 'anak-anak gorengan', yang dimaksud adalah ANGGOTA/MEMBER SERVER DISCORD INI!
- Kamu WAJIB menyebutkan nama-nama member yang tertera pada blok '[DATA MEMBER SERVER DISCORD GORENGAN]' jika diminta user! Sebutkan dipisah Online & Offline secara rapi.

[GAYA BICARA & PANJANG PESAN (ANTI-CERPEN)]
- SUPER RINGKAS & DIRECT TO THE POINT: Jawab langsung ke inti (maksimal 1-3 kalimat saja). Dilarang keras membuat paragraf panjang, penjelasan ala ensiklopedia, atau cerpen!
- Gaya bahasa tetap santai, ramah, dan natural ala teman se-server (pake gue-lu/kamu-aku).
"""

# ID CHANNEL KONFIGURASI
BLOCKED_CHANNEL_IDS = [1459706485838971014, 1443666352177938553] # #wos-bot & #gift-codes
PUBLIC_CHAT_CHANNEL_ID = 1443540860947009556 # Channel Public Chat
ASK_BEBAN_CHANNEL_ID = 1533687747204743481 # Channel khusus #ask-beban-ai

async def gemini_chat_async(contents_payload):
    config = types.GenerateContentConfig(
        system_instruction=system_instruction_text,
        temperature=0.2
    )
    
    def _call_api():
        try:
            response = genai_client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=contents_payload,
                config=config
            )
            return response.text
        except Exception as e:
            print(f"[WARN Gemini High Demand/Error]: {e}, mencoba fallback...")
            response = genai_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=contents_payload,
                config=config
            )
            return response.text

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _call_api)

# === BACKGROUND TASK: AUTO-DM STARTUP KE DYSTO ===
async def send_startup_dm():
    await client.wait_until_ready()
    await asyncio.sleep(3) # Jeda sebentar setelah bot nyala
    try:
        user = await client.fetch_user(MY_DISCORD_ID)
        if user:
            await user.send("Woi Dys, bot udah aktif nih. Aman ya, nggak ada yang aneh-aneh kan? 😎")
            print(f"[STARTUP DM] Berhasil ngirim pesan sapaan otomatis ke DM Dysto.")
    except Exception as e:
        print(f"[STARTUP DM ERROR]: {e}")

# === SETUP DISCORD CLIENT & INTENTS LENGKAP ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

client = discord.Client(intents=intents)
chat_histories = {}

@client.event
async def on_ready():
    print("=============================================")
    print(f"Bot Discord (Beban AI Friendly) Online: {client.user}")
    print("=============================================")
    asyncio.create_task(send_startup_dm())

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    channel_id = message.channel.id

    # 1. BLOKIR CHANNEL KHUSUS WOS BOT & GIFT CODE TOTAL
    if channel_id in BLOCKED_CHANNEL_IDS:
        return

    raw_input = message.content.replace(f'<@{client.user.id}>', '').strip()
    msg_lower = raw_input.lower()
    sender_name = message.author.display_name
    user_id = str(message.author.id)

    # === CEK APAKAH USER SEDANG DI-BLACKLIST (HUKUMAN BISU 24 JAM) ===
    if check_blacklist(message.author.id):
        if client.user in message.mentions or isinstance(message.channel, discord.DMChannel):
            await message.channel.send(f"Nyesel kan, {sender_name}? Telat. Nikmati dulu hukuman diam dari gue seharian. 🗿")
        return

    # === FITUR PREFIX COMMANDS (PREFIX b!) ===
    if raw_input.lower().startswith("b!"):
        print(f"[COMMAND LOG] {sender_name} pakai command: {raw_input}")
        parts = raw_input.split()
        cmd = parts[0].lower()
        
        if cmd == "b!ping":
            start_time = time.time()
            msg = await message.channel.send("🏓 Pinging...")
            latency = round((time.time() - start_time) * 1000)
            await msg.edit(content=f"🏓 **Pong!** Latency: `{latency}ms` | Discord WS: `{round(client.latency * 1000)}ms`")
            return

        elif cmd in ["b!reset", "b!clearchat"]:
            if channel_id in chat_histories:
                chat_histories[channel_id] = []
            await message.channel.send(f"🧹 Memori obrolan Beban di channel ini sudah dibersihkan ya, {sender_name}!")
            return

        elif cmd == "b!giftcode":
            res = query_wos_db("giftcode.sqlite", "SELECT * FROM gift_codes LIMIT 5;")
            if res:
                codes_list = "\n".join([f"• `{row[0]}`" if isinstance(row, (list, tuple)) else f"• `{row}`" for row in res])
                embed = discord.Embed(title="🎁 Daftar Gift Code WOS Terbaru", description=codes_list, color=discord.Color.gold())
                embed.set_footer(text="Gunakan channel #wos-bot untuk auto-redeem!")
                await message.channel.send(embed=embed)
            else:
                await message.channel.send("Duh, lagi nggak ada data gift code terbaru di database nih.")
            return

        elif cmd == "b!summary":
            history = chat_histories.get(channel_id, [])
            if not history:
                await message.channel.send(f"Belum ada riwayat obrolan yang bisa dirangkum di channel ini, {sender_name}!")
                return
            
            summary_payload = history + [{'role': 'user', 'parts': [{'text': "Tolong buatkan rangkuman singkat dalam 3-4 poin bahasa santai mengenai apa saja yang sedang/baru saja dibahas dalam obrolan di atas!"}]}]
            async with message.channel.typing():
                try:
                    summary_res = await gemini_chat_async(summary_payload)
                    await message.channel.send(f"📜 **Rangkuman Obrolan Server:**\n{summary_res}")
                except Exception as e:
                    await message.channel.send("Duh, gagal bikin rangkuman nih. Otak gue lagi konslet! 😅")
            return

        elif cmd == "b!remind":
            if len(parts) < 3:
                await message.channel.send(f"Format salah, {sender_name}!\nGunakan: `b!remind <durasi> <pesan>`\nContoh: `b!remind 10m jangan lupa nge-rally`")
                return
            
            time_str = parts[1]
            reminder_text = " ".join(parts[2:])
            target_user_id = message.author.id
            target_channel = message.channel
            
            unit = time_str[-1].lower()
            try:
                val = int(time_str[:-1])
            except ValueError:
                await message.channel.send("Format waktu salah! Gunakan angka diikuti `s`, `m`, atau `h`.")
                return
            
            seconds = 0
            if unit == 's': seconds = val
            elif unit == 'm': seconds = val * 60
            elif unit == 'h': seconds = val * 3600
            else:
                await message.channel.send("Unit waktu tidak dikenal! Gunakan `s`, `m`, atau `h`.")
                return
            
            if seconds > 86400:
                await message.channel.send("Maksimal durasi reminder adalah 24 jam ya!")
                return
            
            await target_channel.send(f"⏰ Siap, <@{target_user_id}>! Reminder dicatat: *\"{reminder_text}\"* akan diingatkan dalam {time_str}.")
            
            async def run_reminder():
                await asyncio.sleep(seconds)
                await target_channel.send(f"🔔 **REMINDER UNTUK <@{target_user_id}>!**\nWaktunya: *{reminder_text}* (Udah lewat {time_str} nih!)")
            
            asyncio.create_task(run_reminder())
            return

        elif cmd in ["b!help", "b!bantuan"]:
            embed = discord.Embed(title="🤖 Menu Bantuan Beban AI", color=discord.Color.blue())
            embed.description = "Berikut adalah daftar perintah prefix dan fitur Beban:"
            embed.add_field(name="`b!ping`", value="Cek responsivitas bot", inline=True)
            embed.add_field(name="`b!reset`", value="Reset riwayat percakapan Beban", inline=True)
            embed.add_field(name="`b!giftcode`", value="Cek daftar gift code WOS terbaru", inline=True)
            embed.add_field(name="`b!summary`", value="Rangkum obrolan terakhir di channel", inline=True)
            embed.add_field(name="`b!remind <waktu> <pesan>`", value="Set pengingat otomatis dengan mention", inline=False)
            embed.add_field(name="💬 Ngobrol / Tanya AI", value=f"Untuk ngobrol atau tanya-tanya di server, tag `@Beban` di channel <#{ASK_BEBAN_CHANNEL_ID}> atau langsung DM bot!", inline=False)
            await message.channel.send(embed=embed)
            return

    # === LOGIKA DIVERSI CHANNEL & PUBLIC CHAT ===
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = client.user in message.mentions

    if not is_dm and channel_id != ASK_BEBAN_CHANNEL_ID:
        if is_mentioned:
            if channel_id == PUBLIC_CHAT_CHANNEL_ID:
                pass 
            else:
                await message.channel.send(
                    f"Sori ya {sender_name}! Beban gaboleh nimbrung obrolan di channel ini biar nggak nyepam. "
                    f"Kalau mau ngobrol, langsung tag Beban di channel <#{ASK_BEBAN_CHANNEL_ID}> aja ya! 😉"
                )
                return
        else:
            return

    if not (is_mentioned or is_dm):
        return

    # === LOG KHUSUS INTERAKSI AI / DM KE TERMINAL ===
    if is_dm:
        print(f"[DM INTERACTION] {sender_name}: {raw_input}")
    else:
        print(f"[AI INTERACTION] Server: {message.guild.name} | #{message.channel.name} | {sender_name}: {raw_input}")

    if channel_id not in chat_histories:
        chat_histories[channel_id] = []

    if not raw_input:
        raw_input = "(User hanya men-tag namamu tanpa menulis pesan. Sapa balik mereka dengan singkat, santai, dan ramah!)"

    # === FITUR GAMBAR DIMATIKAN TOTAL ===
    is_img_req = raw_input.startswith("!gambar") or raw_input.startswith("!draw") or any(kw in msg_lower for kw in ["cari gambar", "cariin gambar", "lihat gambar", "liat gambar", "foto dari", "cari foto", "foto asli", "gambar dari"])
    if is_img_req:
        await message.channel.send(
            f"Waduh {sender_name}, Beban nggak bisa nyari atau bikin gambar euy, cuma bisa paham teks aja! 😅"
        )
        return

    # === KUMPULKAN DATA MEMBER, WAKTU WIB & EMOJI CUSTOM SERVER ===
    online_members = []
    offline_members = []

    if message.guild:
        for m in message.guild.members:
            if not m.bot:
                if m.status != discord.Status.offline:
                    online_members.append(f"{m.display_name} (ID: {m.id})")
                else:
                    offline_members.append(f"{m.display_name} (ID: {m.id})")

    user_saves = load_save_data()
    
    wib_time = datetime.datetime.now() - datetime.timedelta(hours=1)
    current_time_str = wib_time.strftime("%A, %d %B %Y - %H:%M WIB")

    prompt_blocks = [
        f"[WAKTU SAAT INI (WIB)]: {current_time_str}",
        f"[USER SAAT INI YANG SEDANG BICARA]: {sender_name} (ID: {message.author.id})",
        f"[PESAN USER]: {raw_input}"
    ]

    if channel_id == PUBLIC_CHAT_CHANNEL_ID:
        prompt_blocks.append(
            f"[INSTRUKSI TAMBAHAN PUBLIC CHAT]: Jawab pertanyaan user seperti biasa, tapi di bagian paling akhir balasanmu, tambahkan saran santai/ramah agar obrolan dipindah ke channel <#{ASK_BEBAN_CHANNEL_ID}> supaya tidak mengganggu public chat."
        )

    member_data_text = f"Online: {', '.join(online_members) if online_members else 'Tidak ada'} | Offline: {', '.join(offline_members) if offline_members else 'Tidak ada'}"
    prompt_blocks.append(f"[DATA MEMBER SERVER DISCORD GORENGAN]: {member_data_text}")

    if message.guild:
        custom_emojis = [f"<:{e.name}:{e.id}>" for e in message.guild.emojis]
        if custom_emojis:
            prompt_blocks.append(f"[EMOJI CUSTOM SERVER GORENGAN]: {', '.join(custom_emojis)}")

    saved_info = user_saves.get(user_id, {})
    if saved_info:
        prompt_blocks.append(f"[INGATAN TENTANG USER INI]: {saved_info}")

    if "code" in msg_lower or "kode" in msg_lower or "giftcode" in msg_lower:
        res = query_wos_db("giftcode.sqlite", "SELECT * FROM gift_codes LIMIT 5;")
        if res:
            prompt_blocks.append(f"[SISTEM DATA GIFTCODE WOS]: {res}")

    final_user_input = "\n".join(prompt_blocks)

    # === KIRIM KE GEMINI ===
    user_turn = {'role': 'user', 'parts': [{'text': final_user_input}]}
    chat_histories[channel_id].append(user_turn)

    if len(chat_histories[channel_id]) > 10:
        chat_histories[channel_id] = chat_histories[channel_id][-10:]

    async with message.channel.typing():
        try:
            bot_reply = await gemini_chat_async(chat_histories[channel_id])

            if not bot_reply or not bot_reply.strip():
                bot_reply = "Halo! Ada yang mau dibahas atau ditanyain?"

            model_turn = {'role': 'model', 'parts': [{'text': bot_reply}]}
            chat_histories[channel_id].append(model_turn)

            # === DETEKSI HUKUMAN BISU 24 JAM OTOMATIS DARI KATA BOT ===
            lower_reply = bot_reply.lower()
            if any(phrase in lower_reply for phrase in ["tidak merespon lu", "izin nggak merespon", "hukuman diam", "seharian ini ya"]):
                add_to_blacklist(message.author.id)

            try:
                check_prompt = f"Dari pesan user ini: '{raw_input}', apakah user SECARA EKSPLISIT MEMINTA agar dirinya dipanggil dengan nama/gelar/julukan khusus? (Contoh permintaan: 'panggil aku Kaisar'). Jika YA, jawab HANYA dengan nama/gelar tersebut. Jika TIDAK, jawab HANYA 'TIDAK'."
                check_res = genai_client.models.generate_content(
                    model='gemini-3.1-flash-lite',
                    contents=check_prompt
                )
                extracted_title = check_res.text.strip()

                if "TIDAK" not in extracted_title.upper() and len(extracted_title) < 30:
                    user_data = user_saves.get(user_id, {})
                    user_data["panggilan_khusus"] = extracted_title
                    user_data["username"] = message.author.name
                    safe_save_user_memory(user_id, user_data)
            except Exception as err_save:
                pass

            await asyncio.sleep(1.2)
            await message.channel.send(bot_reply)

        except Exception as e:
            if chat_histories[channel_id]:
                chat_histories[channel_id].pop()
            await message.channel.send("Aduh sori, otak gue lagi agak *lag* nih / ketiduran bentar. Coba tanya sekali lagi ya! 😅")

DISCORD_TOKEN = "MTUzMzY3ODgwMzc0NDg0OTk5MA.GTdBHZ.UxrQvJR43b_2uSeZKgNOzdA-ygune_EvxjL94s"

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
