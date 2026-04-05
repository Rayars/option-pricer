## Start Backend + Frontend

In terminal 1 (backend):

```bash
cd /home/mingxuan/option-pricer
./.venv/bin/python http_server.py
```

In terminal 2 (frontend):

```bash
cd /home/mingxuan/option-pricer/GUI
npm install
npm run dev
```

Frontend runs on port 5173 and proxies /api/* to http://127.0.0.1:8000.

## Optional: Start Backend from GUI Folder

```bash
cd /home/mingxuan/option-pricer/GUI
npm run api
```