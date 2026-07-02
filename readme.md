1. **edit deployment/env/local.env base on you'r config**
2. **install python3.11**
3. **create virtualenv in you'r root path and activate venv**
4. **install packages dependencies with command python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary -r /deployment/requirements/req-prod.txt**
5. **chmod +x deployment/entrypoints/runserver.sh**
6. **run ./deployment/entrypoints/runserver.sh**
7. **notes: for development and production make files in path deployment/env/production.env and deployment/env/development**


