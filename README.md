# ML Video App

Welcome to the **ML Video App** repository! This project aims to provide a mobile application for Android and iOS that allows users to stream video content, which will be used for training AI models. The app ensures the uniqueness of the video by only allowing users to stream new content, preventing any pre-recorded video uploads.

## Project Overview

The ML Video App processes live-streamed video in real-time, breaking it into segments, checking each segment for quality, and sending valid segments to an AI model for training. The app automates the process of filtering out low-quality video and ensures that only relevant data is sent to the AI system.

## Key Features

1. **Video Capture**: Users can only stream live video, ensuring the uniqueness of each video submission.
2. **Segmenting Video**: The captured video is automatically divided into smaller segments for easier processing.
3. **Quality Control**: Each video segment is checked against defined quality parameters. Segments that do not meet the required standards are discarded.
4. **AI Model Training**: The valid, high-quality video segments are sent to an API for model training, enhancing AI capabilities with real-world data.

## How It Works

### 1. Video Capture
- Users open the app and begin streaming video. The app captures the stream and prepares it for processing.

### 2. Segmentation
- The video stream is divided into smaller chunks (typically 60 seconds long) for easy handling and analysis.

### 3. Quality Check
- Each segment is checked for key quality parameters such as resolution, frame rate, and duration.
- Low-quality segments are discarded, ensuring that only the best video data is processed.

### 4. API Integration
- Valid video segments are sent through an API to an AI model for training. The AI system uses this data to improve its capabilities and accuracy.
  
### 5. Data Privacy
- The app is designed with user privacy in mind. We are committed to ensuring all data is handled responsibly, and user consent is obtained before collecting any data for AI training purposes.

## Future Improvements

- **Multilingual Support**: Expanding the app's functionality to include multiple languages and regions.
- **Advanced Quality Metrics**: Implementing more advanced video quality checks for better precision in segment selection.
- **Model Feedback**: Allowing users to see the results of the model training using their video segments.

## Technology Stack

- **Mobile Application**: Developed for Android and iOS.
- **Backend API**: Handles video segmenting, quality checks, and communication with the AI model.
- **AI Model Training**: Uses OpenAI's technology (or a custom solution) for training and improving the models.

## How to Run the Project

1. Clone the repository:
    ```bash
    git clone https://github.com/pilipandr770/ML_video_app.git
    cd ML_video_app
    ```

2. Set up your environment:
    - Install dependencies:
      ```bash
      pip install -r requirements.txt
      ```

3. Run the project:
    - For development purposes:
      ```bash
      python run.py
      ```

4. The application is now running locally. You can access it at `http://127.0.0.1:5000` in your browser.

## Contributing

We welcome contributions to improve the project! If you have ideas or suggestions, feel free to open an issue or submit a pull request. Here's how you can contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push your changes to your forked repository.
5. Create a pull request to merge your changes into the main repository.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Thank you for checking out the ML Video App! We are excited to see how this project will help improve AI training and contribute to the growing field of machine learning and video data processing.
