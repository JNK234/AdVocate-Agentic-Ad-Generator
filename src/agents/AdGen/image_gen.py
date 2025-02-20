import os
import io
import base64
import requests
from PIL import Image
from datetime import datetime

class SDXLTurboGenerator:
    def __init__(self):
        self.api_key = os.getenv('STABILITY_API_KEY')
        if not self.api_key:
            raise ValueError("STABILITY_API_KEY environment variable is not set")
        self.api_host = 'https://api.stability.ai'
        self.engine_id = 'stable-diffusion-xl-1024-v1-0'
        
    def generate_image(self, prompt, output_dir="Outputs"):
        """
        Generate an image using SDXL-Turbo
        
        Args:
            prompt (str): The image of a girl eating ice cream
            output_dir (str): Directory to save the generated image
            
        Returns:
            str: Path to the generated image
        """
        # Convert to absolute path if relative
        output_dir = os.path.abspath(output_dir)
        print(f"Saving image to directory: {output_dir}")
        
        # Create directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created output directory: {output_dir}")
            
        print(f"Generating image with prompt: {prompt}")
            
        response = requests.post(
            f"{self.api_host}/v1/generation/{self.engine_id}/text-to-image",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            json={
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7.5,
                "steps": 10,
                "width": 1024,
                "height": 1024,
                "samples": 1
            },
        )
        
        if response.status_code != 200:
            raise Exception(f"Non-200 response: {response.text}")
            
        data = response.json()
        
        # Save the image
        for i, image in enumerate(data["artifacts"]):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(output_dir, f"sdxl_{timestamp}.png")
            print(f"Saving image to: {image_path}")
            
            image_data = base64.b64decode(image["base64"])
            image = Image.open(io.BytesIO(image_data))
            image.save(image_path)
            print(f"Successfully saved image to: {image_path}")
            
            return image_path
