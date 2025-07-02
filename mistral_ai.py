import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import time
import json
import os
from dotenv import load_dotenv
load_dotenv()

class MistralChatApp:
    def __init__(self, root):
        self.root = root
        root.title("Mistral AI Chat")
        
        # API configuration
        self.api_key = os.getenv('API_KEY') 
        self.model = "mistral-large-latest"  # Or other available models
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  
        
        # Chat history display
        self.chat_history = scrolledtext.ScrolledText(root, width=60, height=20, state='normal')
        self.chat_history.pack(padx=10, pady=10)
        self.chat_history.insert(tk.END, "Welcome to Mistral AI Chat!\nType your message below.\n\n")
        self.chat_history.configure(state='disabled')
        
        # User input
        self.user_input = tk.Entry(root, width=50)
        self.user_input.pack(padx=10, pady=5)
        self.user_input.bind("<Return>", self.send_message)
        self.user_input.focus_set()
        
        # Send button
        self.send_button = tk.Button(root, text="Send", command=self.send_message)
        self.send_button.pack(pady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, padx=5, pady=5)
        
    def send_message(self, event=None):
        user_message = self.user_input.get().strip()
        if not user_message:
            return
            
        # Disable input while processing
        self.user_input.config(state='disabled')
        self.send_button.config(state='disabled')
        self.status_var.set("Processing...")
        self.root.update()
        
        # Add user message to chat
        self.chat_history.configure(state='normal')
        self.chat_history.insert(tk.END, f"You: {user_message}\n")
        self.chat_history.configure(state='disabled')
        self.user_input.delete(0, tk.END)
        
        # Enforce rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        # Call Mistral API
        response = self.call_mistral_api(user_message)
        
        # Add AI response to chat
        self.chat_history.configure(state='normal')
        self.chat_history.insert(tk.END, f"AI: {response}\n\n")
        self.chat_history.configure(state='disabled')
        self.chat_history.see(tk.END)
        
        # Re-enable input
        self.user_input.config(state='normal')
        self.send_button.config(state='normal')
        self.status_var.set("Ready")
        self.user_input.focus_set()
        
    def call_mistral_api(self, message):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": message}]
        }
        
        try:
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            # Update last request time
            self.last_request_time = time.time()
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 5))
                self.status_var.set(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self.call_mistral_api(message)  # Retry
            
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            return response_data["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API Error: {str(e)}"
            if hasattr(e, 'response') and e.response:
                try:
                    error_details = e.response.json()
                    error_msg += f"\nDetails: {json.dumps(error_details, indent=2)}"
                except:
                    error_msg += f"\nStatus: {e.response.status_code}"
            return error_msg
        except Exception as e:
            return f"Unexpected Error: {str(e)}"

if __name__ == "__main__":
    root = tk.Tk()
    app = MistralChatApp(root)
    root.mainloop()