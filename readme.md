# Google Reviews Extractor

## Demo

You can see the project’s running demo here:
[Project Demo](https://drive.google.com/file/d/1pV8F8_wivbrD0PmCGV-PWNjbWWLG-HeW/view?usp=sharing)

## Running the Project Locally

To run the project locally, follow these steps:

1. **Clone the project:**
   Open a terminal and enter:
   ```bash
   git clone https://github.com/Taherpatrawala/google-reviews-extracter.git
   ```

## Backend (Django) Setup

The backend uses Selenium for scraping Google reviews because reviews are loaded dynamically, and BeautifulSoup would not be sufficient.

**NOTE:**

- Ensure you have the latest version of Google Chrome installed on your system.
- When searching using Google search links, Google might detect the automation script if you are running the automation scripts frequently from the same IP. You can run the project without using headless mode to potentially avoid this. To do so, simply comment out the headless option in `scraper/views.py`:
  ```python
  # options.add_argument("--headless")
  ```

Follow these steps to set up the backend:

1. **Navigate to the backend directory:**

   ```bash
   cd backend
   ```

2. **Create a Python virtual environment:**

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install Python dependencies:**
   Ensure you are in the `backend` directory where `requirements.txt` is located.

   ```bash
   pip install -r requirements.txt
   ```

5. **Navigate to the Django project directory:**

   ```bash
   cd gmaps
   ```

6. **Run Django migrations:**

   ```bash
   python manage.py migrate
   ```

7. **Start the development server:**

   ```bash
   python manage.py runserver
   ```

   The backend server will typically start on `http://127.0.0.1:8000/`.

## Frontend (React + TypeScript) Setup

I noticed that foundr.ai uses Neo Brutalism UI style, which just happens to be my new favourite UI design as well, so I thought to make this project’s UI using a similar style.

Open a **new terminal** and follow the steps below:

1. **Navigate to the frontend directory:**

   ```bash
   cd frontend/ui
   ```

2. **Install Node.js dependencies:**

   ```bash
   npm install
   ```

3. **Start the development server:**
   Ensure you are in the `frontend/ui` directory.

   ```bash
   npm run dev
   ```

   The frontend should start running on `http://localhost:5173`.
