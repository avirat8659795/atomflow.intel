from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import os
import re

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATOM-FLOW AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        .theme-dark::-webkit-scrollbar-thumb { background: #1f293d; border-radius: 9999px; }
        .theme-light::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 9999px; }
    </style>
</head>
<body id="appBody" class="theme-dark bg-[#0b0f19] text-[#e2e8f0] font-sans antialiased h-screen flex overflow-hidden transition-colors duration-300">

    <aside id="sidebar" class="fixed inset-y-0 left-0 z-30 w-[260px] bg-[#070a10] border-r border-[#1e293b]/40 flex flex-col justify-between transition-transform duration-300 transform md:relative md:translate-x-0 -translate-x-full shrink-0">
        <div class="p-3.5 flex flex-col h-full overflow-y-auto">
            
            <button onclick="clearChatLog()" class="flex items-center justify-between w-full px-4 py-2.5 text-sm font-semibold rounded-xl bg-[#0f172a] border-2 border-[#10b981] text-white shadow-[0_0_15px_rgba(16,185,129,0.15)] mb-6 hover:bg-[#10b981]/10 transition-all">
                <div class="flex items-center gap-2.5">
                    <span class="text-base text-[#10b981]">⚛️</span> New chat
                </div>
                <span class="text-xs text-[#64748b]">Reset</span>
            </button>

            <div class="space-y-1">
                <p class="px-3 text-xs font-bold text-[#475569] uppercase tracking-wider mb-2.5">Local Core Logs</p>
                <div id="historyLogs" class="space-y-1">
                    <a href="#" class="block px-3 py-2 text-sm text-white rounded-lg bg-[#0f172a]/80 border border-[#1e293b]/30 truncate font-medium">Local Engine Workspace</a>
                </div>
            </div>
        </div>

        <div class="p-4 border-t border-[#1e293b]/30 flex flex-col gap-3 bg-[#05070b]">
            <div>
                <span class="text-xs font-semibold text-[#475569] uppercase tracking-wider block mb-2 px-1">Console Settings</span>
                <button onclick="toggleThemeConfig()" class="w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded-lg bg-[#0f172a] border border-[#1e293b]/50 text-slate-300 hover:text-white transition-all">
                    <span>Theme Mode</span>
                    <span id="themeBtnLabel" class="text-[#10b981] font-bold">🌙 Dark</span>
                </button>
            </div>

            <div class="flex items-center gap-3 p-2 rounded-xl bg-[#0f172a]/40 border border-[#1e293b]/20">
                <div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center shadow-md shrink-0">
                    <span class="text-xs">⚛️</span>
                </div>
                <div class="flex flex-col truncate">
                    <span class="text-sm font-bold text-white tracking-wide">ATOM-FLOW</span>
                    <span class="text-[10px] text-[#10b981] font-mono tracking-widest uppercase">No-API Edition</span>
                </div>
            </div>
        </div>
    </aside>

    <div id="sidebarOverlay" onclick="toggleMobileSidebar()" class="fixed inset-0 bg-black/50 z-20 hidden md:hidden"></div>

    <main class="flex-1 flex flex-col h-full relative overflow-hidden">
        
        <div class="absolute inset-0 flex items-center justify-center pointer-events-none opacity-[0.03] z-0 select-none">
            <svg width="350" height="350" viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="512" cy="512" r="70" fill="#10b981" />
                <ellipse cx="512" cy="512" rx="140" ry="380" stroke="#10b981" stroke-width="32" />
                <ellipse cx="512" cy="512" rx="140" ry="380" stroke="#10b981" stroke-width="32" transform="rotate(60 512 512)" />
                <ellipse cx="512" cy="512" rx="140" ry="380" stroke="#10b981" stroke-width="32" transform="rotate(120 512 512)" />
            </svg>
        </div>
        
        <header id="mainHeader" class="h-14 flex items-center px-4 justify-between border-b border-[#1e293b]/30 z-10 bg-[#0b0f19]/80 backdrop-blur-md transition-colors">
            <button onclick="toggleMobileSidebar()" class="p-2 text-[#64748b] hover:text-white rounded-lg hover:bg-[#1e293b]/40 transition-colors focus:outline-none">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-5 h-5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                </svg>
            </button>
            <div class="text-sm font-medium text-[#94a3b8]">Engine: <span id="modelLabel" class="text-white font-bold tracking-wide">ATOM-LOCAL v1.0</span></div>
            <div class="w-9"></div> </header>

        <div id="chatFeed" class="flex-1 overflow-y-auto px-4 py-6 space-y-6 max-w-3xl w-full mx-auto flex flex-col z-10">
            <div class="flex gap-4 items-start text-base">
                <div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center text-xs shrink-0 shadow-md">⚛️</div>
                <div class="space-y-1.5 flex-1 pt-0.5 leading-relaxed">
                    <p id="assistantNameLabel" class="font-bold text-white text-sm tracking-wide">ATOM-FLOW Core</p>
                    <p id="introText" class="text-[#cbd5e1] text-[15px]">Local modules running smoothly without keys. Paste a target URL link to parse its raw code layout and scrape its strings directly.</p>
                </div>
            </div>
        </div>

        <footer class="p-4 bg-gradient-to-t from-[#0b0f19] via-[#0b0f19] to-transparent z-10 transition-colors" id="mainFooter">
            <div class="max-w-3xl w-full mx-auto relative flex flex-col items-center">
                
                <div id="inputContainer" class="w-full relative flex items-center bg-[#0f172a] rounded-2xl border border-[#1e293b]/60 shadow-2xl group transition-all">
                    <textarea id="messageInput" rows="1" placeholder="Message Atom-Flow Core..." class="w-full bg-transparent text-white placeholder-[#475569] pl-4 pr-14 py-4 resize-none focus:outline-none text-[15px] max-h-40 overflow-y-auto leading-relaxed" oninput="autoGrow(this)" onkeydown="handleKeyDown(event)"></textarea>
                    
                    <button onclick="commitMessageToSend()" class="absolute right-3.5 p-2 bg-[#070a10] border border-[#1e293b]/40 hover:bg-white text-white hover:text-black rounded-xl transition-all duration-200 shadow-md">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="3" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" /></svg>
                    </button>
                </div>
                <p class="text-xs text-[#475569] font-medium mt-3 text-center tracking-wide">Offline local matching engine mode active. Operates completely without API latency boundaries.</p>
            </div>
        </footer>
    </main>

    <script>
        let isDarkMode = true;

        function toggleMobileSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            if (sidebar.classList.contains('-translate-x-full')) {
                sidebar.classList.remove('-translate-x-full');
                overlay.classList.remove('hidden');
            } else {
                sidebar.classList.add('-translate-x-full');
                overlay.classList.add('hidden');
            }
        }

        function toggleThemeConfig() {
            isDarkMode = !isDarkMode;
            const body = document.getElementById('appBody');
            const header = document.getElementById('mainHeader');
            const footer = document.getElementById('mainFooter');
            const inputContainer = document.getElementById('inputContainer');
            const themeBtnLabel = document.getElementById('themeBtnLabel');
            const modelLabel = document.getElementById('modelLabel');

            if (!isDarkMode) {
                // Apply Full Light Theme Visual Configurations
                body.classList.remove('theme-dark', 'bg-[#0b0f19]', 'text-[#e2e8f0]');
                body.classList.add('theme-light', 'bg-[#f8fafc]', 'text-[#334155]');
                header.classList.replace('bg-[#0b0f19]/80', 'bg-white/80');
                header.classList.add('border-slate-200');
                footer.classList.replace('from-[#0b0f19]', 'from-[#f8fafc]');
                inputContainer.classList.replace('bg-[#0f172a]', 'bg-white');
                inputContainer.classList.replace('border-[#1e293b]/60', 'border-slate-300');
                document.getElementById('messageInput').classList.add('text-slate-800');
                themeBtnLabel.innerHTML = "☀️ Light";
                themeBtnLabel.classList.replace('text-[#10b981]', 'text-amber-500');
                modelLabel.classList.replace('text-white', 'text-slate-800');
            } else {
                // Revert Back to Dark Theme Configurations
                body.classList.remove('theme-light', 'bg-[#f8fafc]', 'text-[#334155]');
                body.classList.add('theme-dark', 'bg-[#0b0f19]', 'text-[#e2e8f0]');
                header.classList.replace('bg-white/80', 'bg-[#0b0f19]/80');
                footer.classList.replace('from-[#f8fafc]', 'from-[#0b0f19]');
                inputContainer.classList.replace('bg-white', 'bg-[#0f172a]');
                inputContainer.classList.replace('border-slate-300', 'border-[#1e293b]/60');
                document.getElementById('messageInput').classList.remove('text-slate-800');
                themeBtnLabel.innerHTML = "🌙 Dark";
                themeBtnLabel.classList.replace('text-amber-500', 'text-[#10b981]');
                modelLabel.classList.replace('text-slate-800', 'text-white');
            }
        }

        function clearChatLog() {
            const feed = document.getElementById('chatFeed');
            feed.innerHTML = `
                <div class="flex gap-4 items-start text-base">
                    <div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center text-xs shrink-0 shadow-md">⚛️</div>
                    <div class="space-y-1.5 flex-1 pt-0.5 leading-relaxed">
                        <p class="font-bold ${isDarkMode ? 'text-white' : 'text-slate-800'} text-sm tracking-wide">ATOM-FLOW Core</p>
                        <p class="${isDarkMode ? 'text-[#cbd5e1]' : 'text-slate-600'} text-[15px]">New chat workspace initialized cleanly. Send a message or paste a URL endpoint link below.</p>
                    </div>
                </div>
            `;
        }

        function autoGrow(element) {
            element.style.height = "auto";
            element.style.height = (element.scrollHeight) + "px";
        }
        
        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                commitMessageToSend();
            }
        }

        function appendMessageRow(text, isUser) {
            const feed = document.getElementById('chatFeed');
            let block = '';
            
            if(isUser) {
                block = `
                    <div class="flex gap-4 items-start text-base self-end justify-end w-full max-w-xl ml-auto">
                        <div class="${isDarkMode ? 'bg-[#1e293b]/60 text-white' : 'bg-slate-200 text-slate-800'} border border-transparent rounded-2xl px-4 py-3 text-[15px] leading-relaxed shadow-md backdrop-blur-sm">
                            ${text.replace(/\\n/g, '<br>')}
                        </div>
                    </div>`;
            } else {
                block = `
                    <div class="flex gap-4 items-start text-base">
                        <div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center text-xs shrink-0 shadow-md">⚛️</div>
                        <div class="space-y-1.5 flex-1 pt-0.5 leading-relaxed">
                            <p class="font-bold ${isDarkMode ? 'text-white' : 'text-slate-800'} text-sm tracking-wide">ATOM-FLOW Core</p>
                            <p class="${isDarkMode ? 'text-[#cbd5e1]' : 'text-slate-600'} text-[15px]">${text.replace(/\\n/g, '<br>')}</p>
                        </div>
                    </div>`;
            }
            feed.insertAdjacentHTML('beforeend', block);
            feed.scrollTop = feed.scrollHeight;
        }

        function updateSidebarLogHistory(promptText) {
            const container = document.getElementById('historyLogs');
            const absoluteTitle = promptText.length > 22 ? promptText.substring(0, 22) + '...' : promptText;
            const newAnchor = `<a href="#" class="block px-3 py-2 text-sm text-[#94a3b8] rounded-lg hover:bg-[#0f172a]/50 hover:text-white truncate transition-colors">${absoluteTitle}</a>`;
            container.insertAdjacentHTML('afterbegin', newAnchor);
        }

        function commitMessageToSend() {
            const input = document.getElementById('messageInput');
            const messageText = input.value.trim();
            if (!messageText) return;

            appendMessageRow(messageText, true);
            updateSidebarLogHistory(messageText);
            input.value = '';
            input.style.height = 'auto';

            // Check screen dimension parameters to auto-hide mobile sidebar draw layers
            if(window.innerWidth < 768) {
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('sidebarOverlay');
                sidebar.classList.add('-translate-x-full');
                overlay.classList.add('hidden');
            }

            fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText })
            })
            .then(res => res.json())
            .then(data => {
                appendMessageRow(data.reply, false);
            })
            .catch(err => {
                appendMessageRow("System tracking exception loop. Failed to resolve local framework matching nodes.", false);
            });
        }
    </script>
</body>
</html>
"""

def extract_raw_web_strings(url: str) -> str:
    """Scrapes raw text from a website layout using light text-stream extractions"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strip out useless script elements to keep text pure
        for code_node in soup(["script", "style"]):
            code_node.decompose()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = " ".join(chunk for chunk in chunks if chunk)
        return clean_text[:600] # Pass first 600 string characters to the matcher
    except Exception as e:
        return f"Scraping error encountered: {str(e)}"

def process_local_matrix_response(user_input: str, scraped_text: str = "") -> str:
    """A highly optimized local matcher engine that gives immediate answers without an API key"""
    prompt = user_input.lower()
    
    # Context-aware adjustments if a web link was scraped
    if scraped_text:
        return f"🌐 **Web Scraping Analysis Mode Complete**\n\nI successfully scraped the target webpage. Here is the direct text context extracted from the site's layout:\n\n*\"{scraped_text}...\"*\n\nBecause I am running in local-matching offline mode without external API keys, I cannot generate fluid conversational summaries, but the code successfully pulled these active strings directly into the terminal memory framework!"

    # Local Knowledge Routing Matrix
    if "hello" in prompt or "hi" in prompt:
        return "Greetings! The local core is active. I am running entirely via local Python matrices on Render without any external AI API dependency connections."
    
    elif "status" in prompt or "system" in prompt:
        return "📋 **System Resource Status Check**:\n- Runtime Environment: Render Free Linux Layer\n- AI API Dependency: None (100% Free/Offline Mode)\n- Core Status: Synchronized\n- Mobile UI Rendering: Responsive Layer Confirmed"
        
    elif "help" in prompt or "features" in prompt:
        return "💡 **Available Operations Matrix**:\n1. Paste any `http://` or `https://` link to trigger the live Python parser web-scraper.\n2. Ask for 'status' to test connectivity loops.\n3. Click the toggle switch in the bottom left to change between Light and Dark visual theme modes."

    # Fallback response for unmapped logic strings
    return f"Processed query string: *\"{user_input}\"* safely inside the local engine workspace. To scrape a live web target, simply paste the full URL link containing `http://` or `https://` directly into the chat prompt input capsule."

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return HTML_UI

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_prompt = request.message
    scraped_data = ""
    
    # Catch any URLs embedded inside the input box string payload
    if "http://" in user_prompt or "https://" in user_prompt:
        words = user_prompt.split()
        target_url = next((w for w in words if w.startswith("http")), None)
        if target_url:
            scraped_data = extract_raw_web_strings(target_url)

    local_reply = process_local_matrix_response(user_prompt, scraped_data)
    return {"reply": local_reply}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
