from flask import Flask, request, jsonify
import base64
import cv2

app = Flask(__name__)

IMAGE_PATH = "input_images/temp_page_1.jpg"
# IMAGE_PATH = "sample.jpg"

@app.route("/")
def index():
    with open(IMAGE_PATH, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")

    return f"""
    <html>
    <body>
        <h2>Draw boxes on image</h2>
        <canvas id="canvas"></canvas>
        <script>
            const img = new Image();
            img.src = "data:image/jpeg;base64,{img_data}";

            const canvas = document.getElementById("canvas");
            const ctx = canvas.getContext("2d");

            let startX, startY, drawing = false;
            let rects = [];

            img.onload = () => {{
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
            }};

            canvas.onmousedown = (e) => {{
                startX = e.offsetX;
                startY = e.offsetY;
                drawing = true;
            }};

            canvas.onmouseup = (e) => {{
                if (!drawing) return;
                drawing = false;

                const x = Math.min(startX, e.offsetX);
                const y = Math.min(startY, e.offsetY);
                const w = Math.abs(e.offsetX - startX);
                const h = Math.abs(e.offsetY - startY);

                rects.push({{x, y, w, h}});

                ctx.strokeStyle = "red";
                ctx.strokeRect(x, y, w, h);

                const rel = [
                    (x / canvas.width).toFixed(4),
                    (y / canvas.height).toFixed(4),
                    (w / canvas.width).toFixed(4),
                    (h / canvas.height).toFixed(4)
                ];

                console.log("Relative:", rel);
            }};
        </script>
    </body>
    </html>
    """
    

if __name__ == "__main__":
    app.run(port=5000)