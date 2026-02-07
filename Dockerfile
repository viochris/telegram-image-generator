# KITA PAKAI IMAGE FULL (Bukan Slim)
# Ukurannya besar, tapi driver internet & DNS-nya lengkap bawaan pabrik.
FROM python:3.9

# Set folder kerja
WORKDIR /code

# Copy file requirements
COPY ./requirements.txt /code/requirements.txt

# Install library
# Kita tambah --upgrade pip biar instalasinya lancar
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /code/requirements.txt

# Set User ID 1000 (Standar Wajib Hugging Face Spaces)
# Ini supaya tidak kena error "Permission Denied"
RUN useradd -m -u 1000 user
USER user

# Set Environment Variables buat User
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Pindah ke folder User
WORKDIR $HOME/app

# Copy semua file codingan ke folder User dan ganti pemiliknya jadi 'user'
COPY --chown=user . $HOME/app

# JALANKAN BOT
# Pastikan nama file ini BENAR sesuai nama file kamu
CMD ["python", "img_maker_tele.py"]