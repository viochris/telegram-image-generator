# WE USE THE FULL IMAGE (Not Slim)
# Larger size, but includes complete internet drivers & DNS configuration out-of-the-box.
FROM python:3.11

# Set working directory
WORKDIR /code

# Copy requirements file
COPY ./requirements.txt /code/requirements.txt

# Install libraries
# We upgrade pip first to ensure smooth installation
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /code/requirements.txt

# Set User ID 1000 (Mandatory Standard for Hugging Face Spaces)
# This prevents "Permission Denied" errors
RUN useradd -m -u 1000 user
USER user

# Set Environment Variables for the User
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Switch to User directory
WORKDIR $HOME/app

# Copy all application files to the User directory and change ownership to 'user'
COPY --chown=user . $HOME/app

# RUN THE BOT
# Ensure this filename MATCHES your actual Python file
CMD ["python", "img_maker_tele.py"]
