import time
from flask import Flask, send_file, request
import pyautogui
from io import BytesIO

app = Flask(__name__)

import cv2 # type: ignore
import numpy as np

@app.route("/video_feed")
def video_feed():
    def generate():
        while True:
            try:
                img = pyautogui.screenshot()
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                if not ret:
                    continue
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(1 / 60)  # 30 FPS
            except Exception as e:
                print("Video stream error:", e)
                break

    return app.response_class(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/screen")
def screen():
    try:
        img = pyautogui.screenshot()
        img_io = BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')
    except Exception as e:
        print("Screenshot error:", e)
        return f"Error: {e}", 500

@app.route("/click", methods=["POST"])
def click():
    try:
        if request.content_type == "application/json":
            data = request.json
            button = data.get("button", "left")
            print(f"🖱️ JSON click {button}")
            pyautogui.click(button=button)
            return "Clicked"
        else:
            x = int(request.form["x"])
            y = int(request.form["y"])
            print(f"🖱️ Moving and clicking at ({x}, {y})")
            pyautogui.moveTo(x, y)
            pyautogui.click()
            return "Clicked"
    except Exception as e:
        print("Click error:", e)
        return f"Error: {e}", 500

@app.route("/move_mouse", methods=["POST"])
def move_mouse():
    try:
        data = request.json
        dx = int(data.get("dx", 0))
        dy = int(data.get("dy", 0))
        print(f"🖱️ Moving mouse by ({dx}, {dy})")
        pyautogui.moveRel(dx, dy)
        return "Moved"
    except Exception as e:
        print("Move error:", e)
        return f"Error: {e}", 500

@app.route("/type", methods=["POST"])
def type_keys():
    try:
        keys = request.form["keys"]
        print(f"⌨️ Typing: {keys}")
        pyautogui.write(keys)
        return "Typed"
    except Exception as e:
        print("Typing error:", e)
        return f"Error: {e}", 500

@app.route("/home", methods=["POST"])
def home_desktop():
    try:
        print("🏠 Showing desktop (Win + D)")
        pyautogui.hotkey('win', 'd')
        return "Desktop Shown"
    except Exception as e:
        print("Home button error:", e)
        return f"Error: {e}", 500

@app.route("/scroll", methods=["POST"])
def scroll():
    try:
        data = request.json
        delta = int(float(data.get("deltaY", 0)))
        print(f"🖱️ Scrolling: {delta}")
        pyautogui.scroll(-delta)  # negative = down
        return "Scrolled"
    except Exception as e:
        print("Scroll error:", e)
        return f"Error: {e}", 500

@app.route("/mouse_position")
def mouse_position():
    try:
        x, y = pyautogui.position()
        return { "x": x, "y": y }
    except Exception as e:
        print("Mouse position error:", e)
        return { "x": 0, "y": 0 }


@app.route("/")
def index():
    return '''
    <html>
    <head><title>Remote PC</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
    <style>
      body { margin:0; background:black; color:white; font-family:sans-serif; text-align:center; }
      #screen { width:100vw; height:auto; display:block; touch-action:none; }
      #touchpad {
        width: 100vw;
        height: 200px;
        background: #222;
        margin-top: 10px;
        touch-action: none;
      }
      #touchpad p { color: #777; font-size: 14px; padding-top: 80px; }
      input { padding:8px; font-size:16px; width:90%; margin:10px auto; display:block; }
      button { padding:10px 20px; font-size:16px; margin:10px; border-radius:8px; }

      #cursor {
  position: fixed;
  top: 0;
  left: 0;
  width: 20px;
  height: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  pointer-events: none;
  z-index: 9999;
  transition: transform 0.15s ease-out;
  transition: transform 0.12s ease-out;

}


  /* Make cursor larger on small screens (phones) */
  @media (max-width: 768px) {
    #cursor {
      width: 7px;
      height: 7px;
    }
  }

  /* Even bigger for ultra-small devices if needed */
  @media (max-width: 480px) {
    #cursor {
      width: 4px;
      height: 4px;
    }
  }

  #modeBtn {
  padding: 10px 20px;
  font-size: 16px;
  margin: 10px;
  border-radius: 8px;
  background: #444;
  color: white;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}

#modeBtn:hover {
  background: #666;
}

    </style>
    </head>
    <body>
    <div id="cursor"></div>


      <h3>📱 Remote PC</h3>
     <div id="screenWrapper">
  <img id="screen" src="/video_feed" onclick="sendClick(event)" />
</div>

     <button onclick="toggleMode()" id="modeBtn">🔁 Switch to Screenshot Mode</button>
     <script>
  let usingVideo = true;
  let streamInterval = null;

  function toggleMode() {
    const screen = document.getElementById("screen");
    const btn = document.getElementById("modeBtn");

    if (usingVideo) {
      // Switch to Screenshot Mode
      screen.src = "/screen?" + new Date().getTime();
      streamInterval = setInterval(() => {
        screen.src = "/screen?" + new Date().getTime();
      }, 1000);
      btn.innerText = "🔁 Switch to Video Mode";
    } else {
      // Switch to Video Mode
      if (streamInterval) clearInterval(streamInterval);
      screen.src = "/video_feed";
      btn.innerText = "🔁 Switch to Screenshot Mode";
    }

    usingVideo = !usingVideo;
  }
</script>

      <div id="touchpad"><p>🖲️ Touchpad Area</p></div>
      <div>
        <button onclick="sendClickButton('left')">Left Click</button>
        <button onclick="sendClickButton('right')">Right Click</button>
      </div>
      <input id="keyInput" placeholder="Type here..." oninput="sendKeys(this.value); this.value=''" />
      <button onclick="toggleStreaming()" id="toggleBtn">🛑 Stop View</button>
      <button onclick="goHome()">🏠 Show Desktop</button>

      <script>
        let streaming = true;
        let interval = null;

        function startStream() {
          stopStream();
          interval = setInterval(() => {
            const img = document.getElementById("screen");
            img.src = "/screen?" + new Date().getTime();
          }, 1000);
          document.getElementById("toggleBtn").innerText = "🛑 Stop View";
        }

        function stopStream() {
          if (interval) clearInterval(interval);
          interval = null;
          document.getElementById("toggleBtn").innerText = "▶️ Resume View";
        }

        function toggleStreaming() {
          streaming = !streaming;
          if (streaming) startStream();
          else stopStream();
        }

        function sendClick(e) {
          const img = document.getElementById("screen");
          const rect = img.getBoundingClientRect();
          const naturalW = img.naturalWidth;
          const naturalH = img.naturalHeight;

          if (!naturalW || !naturalH) return;

          const scaleX = naturalW / rect.width;
          const scaleY = naturalH / rect.height;

          const x = Math.round((e.clientX - rect.left) * scaleX);
          const y = Math.round((e.clientY - rect.top) * scaleY);

          fetch("/click", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: "x=" + x + "&y=" + y
          });
        }

        function sendClickButton(button) {
          fetch("/click", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ button: button })
          });
        }

        function sendKeys(val) {
          fetch("/type", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: "keys=" + encodeURIComponent(val)
          });
        }

        function goHome() {
          fetch("/home", { method: "POST" });
        }

        // 🖱️ TOUCHPAD LOGIC
        let lastX = 0, lastY = 0;
const pad = document.getElementById("touchpad");

pad.addEventListener("touchstart", (e) => {
  if (e.touches.length === 1) {
    lastX = e.touches[0].clientX;
    lastY = e.touches[0].clientY;
  } else if (e.touches.length === 2) {
    lastY = (e.touches[0].clientY + e.touches[1].clientY) / 2;
  }
});

pad.addEventListener("touchmove", (e) => {
  e.preventDefault();
  if (e.touches.length === 1) {
    const t = e.touches[0];
    const dx = t.clientX - lastX;
    const dy = t.clientY - lastY;
    lastX = t.clientX;
    lastY = t.clientY;

    fetch("/move_mouse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dx: dx, dy: dy })
    });
  } else if (e.touches.length === 2) {
    const currentY = (e.touches[0].clientY + e.touches[1].clientY) / 2;
    const deltaY = currentY - lastY;
    lastY = currentY;

    fetch("/scroll", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ deltaY: deltaY })
    });
  }
}, { passive: false });


        startStream();
        function updateCursorPosition() {
  fetch("/mouse_position")
    .then(res => res.json())
    .then(pos => {
      const img = document.getElementById("screen");
      const rect = img.getBoundingClientRect();
      const naturalW = img.naturalWidth;
      const naturalH = img.naturalHeight;

      const scaleX = rect.width / naturalW;
      const scaleY = rect.height / naturalH;

      const screenX = pos.x * scaleX + rect.left;
      const screenY = pos.y * scaleY + rect.top;

      const cursor = document.getElementById("cursor");
      cursor.style.transform = `translate(${screenX}px, ${screenY}px)`;
    });
}

setInterval(updateCursorPosition, 16);  // Update every 100ms

      </script>
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888)
