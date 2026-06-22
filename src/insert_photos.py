import sqlite3
import base64
import os

images = {
    "Hambúrguer Artesanal": r"C:\Users\isaque.santos\.gemini\antigravity\brain\e5d69ef6-09b0-4c35-bd4c-5854c0289e72\burger_1781701330302.png",
    "Pizza Calabresa": r"C:\Users\isaque.santos\.gemini\antigravity\brain\e5d69ef6-09b0-4c35-bd4c-5854c0289e72\pizza_1781701340808.png",
    "Suco de Laranja": r"C:\Users\isaque.santos\.gemini\antigravity\brain\e5d69ef6-09b0-4c35-bd4c-5854c0289e72\juice_1781701351057.png",
    "Coca-Cola Lata": r"C:\Users\isaque.santos\.gemini\antigravity\brain\e5d69ef6-09b0-4c35-bd4c-5854c0289e72\coke_1781701362649.png",
    "Porção de Fritas": r"C:\Users\isaque.santos\.gemini\antigravity\brain\e5d69ef6-09b0-4c35-bd4c-5854c0289e72\fries_1781701373177.png"
}

def get_base64_string(filepath):
    if not os.path.exists(filepath):
        print(f"Not found: {filepath}")
        return None
    with open(filepath, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:image/png;base64,{encoded_string}"

def update_photos():
    conn = sqlite3.connect('apiDatabase.db')
    cursor = conn.cursor()
    
    for name, path in images.items():
        b64 = get_base64_string(path)
        if b64:
            # We must pass bytes or text. In Python, SQLite accepts strings.
            # But the schema uses LargeBinary. Let's pass the string directly.
            cursor.execute("UPDATE tb_produto SET foto = ? WHERE nome = ?", (b64, name))
            print(f"Updated {name}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_photos()
