import os
import threading
import re
from html.parser import HTMLParser
from flask import Flask, render_template_string, jsonify, request
from mailtm import Email

app = Flask(__name__)

# Folder for saving emails /
MAIL_FOLDER = os.path.join(os.getcwd(), 'mails')
os.makedirs(MAIL_FOLDER, exist_ok=True)

# Global application state
app_state = {
    "email": None,
    "domain": None,
    "messages": [],
    "save_to_files": False,
    "status": "Initializing..."
}

mail_client = None

class HTMLFilter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

def clean_html(raw_html):
    if not raw_html:
        return ""
    parser = HTMLFilter()
    try:
        parser.feed(raw_html)
        return "".join(parser.text).strip()
    except Exception:
        return raw_html

def listener(message):
    print("-----------------")
    subject = message.get('subject', 'Without a subject')
    print(f"\nEmail arrived: {subject}")

    raw_text = message.get('text')
    raw_html = message.get('html')

    if raw_text:
        text_content = raw_text
    elif raw_html:
        text_content = clean_html(raw_html)
    else:
        text_content = ""

    sender = message.get('from', {}).get('address', 'Couldnt find any sender') if isinstance(message.get('from'), dict) else str(message.get('from'))

    new_msg = {
        "id": message.get('id', str(len(app_state["messages"]) + 1)),
        "subject": subject,
        "from": sender,
        "content": text_content,
        "date": message.get('createdAt', 'Right now')
    }

    app_state["messages"].insert(0, new_msg)

    # Saving email content to the /mails folder in the format: subject-senderemail.txt
    if app_state["save_to_files"]:
        safe_subject = "".join(c for c in new_msg['subject'] if c.isalnum() or c in (' ', '_', '-')).strip()
        if not safe_subject:
            safe_subject = "without-subject"

        safe_sender = "".join(c for c in new_msg['from'] if c.isalnum() or c in (' ', '_', '-', '@', '.')).strip()
        if not safe_sender:
            safe_sender = "Unknown"

        filename = f"{safe_subject}-{safe_sender}.txt"
        file_path = os.path.join(MAIL_FOLDER, filename)

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(text_content)
            print(f"Saved to: {file_path}")
        except Exception as e:
            print(f"Error while saving a email: {e}")

def init_mail_account():
    global mail_client
    try:
        app_state["status"] = "Connecting to mail.tm..."
        mail_client = Email()
        app_state["domain"] = mail_client.domain
        mail_client.register()
        app_state["email"] = mail_client.address
        app_state["status"] = "Listening for emails..."

        # Starting the listener in the background
        mail_client.start(listener)
    except Exception as e:
        app_state["status"] = f"Error: {str(e)}"

#The look of the website c:
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BMail WebUI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
        }
    </script>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen flex flex-col font-sans selection:bg-indigo-500 selection:text-white">

    <!-- Navbar -->
    <header class="border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md py-3 px-4 sm:px-6 flex justify-between items-center sticky top-0 z-10">
        <div class="flex items-center space-x-3">
            <h1 class="text-sm font-semibold tracking-tight text-zinc-200">BMail</h1>
        </div>
        <div class="flex items-center space-x-2 sm:space-x-4">
            <span id="connection-status" class="text-[11px] sm:text-xs px-2 sm:px-2.5 py-1 bg-zinc-900 border border-zinc-800 text-zinc-400 rounded-md font-mono truncate max-w-[120px] sm:max-w-none">Loading...</span>
            <button onclick="createNewEmail()" class="bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 hover:text-white px-3 py-1.5 rounded-lg text-xs font-medium transition active:scale-95">
                New address
            </button>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">

        <!-- left panel: Profile and Settings -->
        <div class="space-y-4 sm:space-y-6">
            <!-- Email box -->
            <div class="bg-zinc-900/40 border border-zinc-800/80 p-4 rounded-xl space-y-2">
                <label class="block text-[11px] font-medium text-zinc-500 uppercase tracking-wider">Active mailbox</label>
                <div class="flex items-center space-x-2 bg-zinc-950 border border-zinc-800/80 p-2 rounded-lg">
                    <input type="text" id="email-address" readonly value="Generating..." class="bg-transparent w-full text-xs font-mono text-zinc-300 focus:outline-none truncate">
                    <button onclick="copyEmail()" class="text-xs font-medium bg-zinc-800 hover:bg-zinc-700 text-zinc-200 px-2.5 py-1 rounded transition shrink-0">Copy</button>
                </div>
            </div>

            <!-- Settings -->
            <div class="bg-zinc-900/40 border border-zinc-800/80 p-4 rounded-xl space-y-4">
                <h3 class="text-[11px] font-medium text-zinc-500 uppercase tracking-wider">Settings</h3>
                <div class="flex items-center justify-between">
                    <span class="text-xs text-zinc-300">Save emails to files</span>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" id="save-toggle" onchange="toggleSaveFiles(this)" class="sr-only peer">
                        <div class="w-8 h-4 bg-zinc-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-zinc-400 after:border-zinc-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-indigo-600"></div>
                    </label>
                </div>
                <div class="text-[11px] text-zinc-500 leading-relaxed">
                    Files are saved to <code class="text-zinc-400 bg-zinc-900 px-1 py-0.5 rounded">/mails</code> in the format <span class="text-zinc-400 italic">subject-senderemail.txt</span>.
                </div>
            </div>
        </div>

        <!-- Right panel: Inbox (Email list) -->
        <div class="md:col-span-2 bg-zinc-900/40 border border-zinc-800/80 rounded-xl flex flex-col h-[65vh] sm:h-[70vh]">
            <div class="p-4 border-b border-zinc-800/80 flex justify-between items-center">
                <h2 class="text-xs font-medium text-zinc-400 uppercase tracking-wider">Inbox</h2>
                <span id="mail-count" class="text-xs font-mono text-zinc-500">0 messages</span>
            </div>

            <div id="messages-container" class="flex-1 overflow-y-auto p-4 space-y-3">
                <div class="text-center text-zinc-600 py-16 text-xs">
                    Waiting for incoming messages...
                </div>
            </div>
        </div>
    </main>

    <script>
        function fetchState() {
            fetch('/api/state')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('email-address').value = data.email || "Loading...";
                    document.getElementById('connection-status').innerText = data.status;

                    if(data.save_to_files) {
                        document.getElementById('save-toggle').checked = true;
                    }

                    renderMessages(data.messages);
                });
        }

        // Helper function for converting URLs to clickable links and HTML injection protection
        function formatMailContent(text) {
            const escapeHtml = (str) => {
                return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            };

            const escaped = escapeHtml(text);
            // Regex for detecting http/https URLs
            const urlRegex = /(https?:\/\/[^\s]+)/g;

            return escaped.replace(urlRegex, function(url) {
                return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-indigo-400 hover:text-indigo-300 underline break-all">${url}</a>`;
            });
        }

        function renderMessages(messages) {
            const container = document.getElementById('messages-container');
            document.getElementById('mail-count').innerText = messages.length + ' messages';

            if (messages.length === 0) {
                container.innerHTML = '<div class="text-center text-zinc-600 py-16 text-xs">Waiting for incoming messages...</div>';
                return;
            }

            container.innerHTML = messages.map(msg => `
                <div class="bg-zinc-950 border border-zinc-800/80 rounded-lg p-3.5 space-y-2">
                    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-1">
                        <div class="overflow-hidden">
                            <span class="text-[10px] font-mono text-indigo-400 uppercase tracking-wider block truncate">${msg.from}</span>
                            <h3 class="font-medium text-zinc-200 text-sm mt-0.5">${msg.subject}</h3>
                        </div>
                        <span class="text-[10px] font-mono text-zinc-600 shrink-0">${msg.date}</span>
                    </div>
                    <div class="text-xs text-zinc-400 bg-zinc-900/50 p-2.5 rounded border border-zinc-800/50 whitespace-pre-wrap font-mono overflow-x-auto">${formatMailContent(msg.content)}</div>
                </div>
            `).join('');
        }

        function copyEmail() {
            const copyText = document.getElementById("email-address");
            copyText.select();
            document.execCommand("copy");
            alert("Email copied to clipboard!");
        }

        function toggleSaveFiles(checkbox) {
            fetch('/api/toggle-save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({save: checkbox.checked})
            });
        }

        function createNewEmail() {
            fetch('/api/new-email', {method: 'POST'})
                .then(() => fetchState());
        }

        setInterval(fetchState, 2000);
        fetchState();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/state')
def get_state():
    return jsonify(app_state)

@app.route('/api/toggle-save', methods=['POST'])
def toggle_save():
    data = request.json
    app_state["save_to_files"] = data.get("save", False)
    return jsonify({"success": True})

@app.route('/api/new-email', methods=['POST'])
def new_email():
    app_state["messages"] = []
    threading.Thread(target=init_mail_account, daemon=True).start()
    return jsonify({"success": True})

if __name__ == '__main__':
    threading.Thread(target=init_mail_account, daemon=True).start()
    print("Starting local WebUI on http://0.0.0.0:8080") #insert 127.0.0.1 as the ip if you want the server to run on ur local ip addres
    app.run(host='0.0.0.0', port=8080, debug=False) #here too
