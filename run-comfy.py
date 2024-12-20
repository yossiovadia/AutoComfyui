import json
import requests
from pathlib import Path
import time

def read_prompts(filename):
    """Read prompts from a JSON file."""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Extract prompt text from each dictionary in the prompts list
        return [prompt["prompt"].strip() for prompt in data["prompts"] if prompt["prompt"].strip()]

def load_workflow(filename):
    """Load the ComfyUI workflow from JSON file."""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def improve_description(prompt):
    """Send a request to Ollama and get back an improved description"""
    url = "http://127.0.0.1:11434/api/generate"
    
    # Construct the prompt text
    enhanced_prompt = f"Only answer, no post or pre explanations. there is a description of photo, please enhance it as follow- Describing the subjects:\nProvide more information about the people, animals, or objects in the photo. This could include their expressions, actions, clothing, or physical characteristics.\nSetting the scene:\nDescribe the background, location, time of day, weather, or any other environmental factors that contribute to the atmosphere of the photo.\nAdding context:\nExplain the situation or story behind the photo. Why are the subjects in this setting? What is happening or about to happen?\nUsing sensory details:\nIncorporate elements that appeal to senses—sight, sound, smell, touch, taste—to make the description more immersive.\nEmploying vivid verbs and adjectives:\nChoose descriptive words that bring the scene to life and create a stronger mental image for the reader.\nCreating mood or emotion:\nSuggest feelings or emotions evoked by the photo, either through subjects' expressions or the overall atmosphere.\n\n{prompt}"
    seed = int(time.time() * 1000) % (2**8)
    payload = {
        'model': 'qwen2.5:14b',
        'prompt': enhanced_prompt,
        'stream': False,
        'options': {"top_p":0.99,"top_k":0.99, "seed": seed}
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get('response', None)
        else:
            print(f"Error from Ollama API (Status Code: {response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"Exception while calling Ollama API: {e}")
        return None

def send_to_comfyui(workflow, prompt, api_url="http://127.0.0.1:8188"):
    """Send a workflow with inserted prompt to ComfyUI API."""
    print("Before improving prompt:")
    print_separator()
    print(prompt)
    print_separator()
    # Improve the description
    improved_prompt = improve_description(prompt)
    
    if not improved_prompt:
        print(f"Failed to improve prompt: {prompt}")
        return None
    
    # Create a deep copy of the workflow to avoid modifying the original
    current_workflow = json.loads(json.dumps(workflow))
    
    # Insert the improved prompt into node 28
    current_workflow["28"]["inputs"]["string"] = improved_prompt
    
    print("Improved prompt:")
    print_separator()
    print(improved_prompt)
    print_separator()
    
    try:
        # Queue the prompt
        response = requests.post(f"{api_url}/prompt", json={"prompt": current_workflow})
        if response.status_code == 200:
            prompt_id = response.json()['prompt_id']
            return prompt_id
        else:
            print(f"Error sending prompt: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return None

def wait_for_completion(prompt_id, api_url="http://127.0.0.1:8188"):
    """Wait for the prompt to complete processing."""
    while True:
        try:
            response = requests.get(f"{api_url}/history/{prompt_id}")
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history and "outputs" in history[prompt_id]:
                    return True
            time.sleep(1)
        except requests.exceptions.RequestException:
            print("Error checking prompt status")
            return False

def update_noise_seed(workflow, seed):
    """Update the noise seed for each run."""
    workflow["25"]["inputs"]["noise_seed"] = seed
    return workflow

def main():
    # File paths
    prompts_file = Path("simple_prompts.json")
    workflow_file = Path("workflow.json")
    
    try:
        # Load workflow and prompts
        workflow = load_workflow(workflow_file)
        
        prompts = read_prompts(prompts_file)
        
        print(f"Successfully loaded {len(prompts)} prompts")
        print(f"Starting processing at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print_separator()
        
        # Process each prompt
        for i, prompt in enumerate(prompts, 1):
            print(f"Prompt {i}/{len(prompts)}")
            
            start_time = time.time()

            # Generate a new random seed
            new_seed = int(time.time() * 1000) % (2**32)
            
            # Update the workflow with the new noise seed
            updated_workflow = update_noise_seed(workflow, new_seed)

            # Send to ComfyUI with improved description
            prompt_id = send_to_comfyui(updated_workflow, prompt)
            
            if prompt_id:
                print(f"⏳ Processing... (ID: {prompt_id})")
                
                if wait_for_completion(prompt_id):
                    end_time = time.time()
                    duration = end_time - start_time
                    print(f"Completed in {duration:.2f} seconds")
                    
    except Exception as e:
        print(f"An error occurred during processing: {e}")

def print_separator():
    """Print a separator line for better readability."""
    print('-' * 80)

if __name__ == "__main__":
    main()