# sentinel

  ## Setup
  
  Download Node.js and add to PATH
  Check npm -v

  Run `pip install npm` (maybe unecessary)
  Run `npm i` to install the dependencies.

  Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` if scripts error appears

  Run `python -m pip install <module>`
    - Module refers to any package that is not recognized or not found
    - (e.g pandas, joblib, geopandas, etc.)
    - You must install all dependencies for backend to work
  

  ## To Run:

  Backend:
  Open a new terminal for the backend to boot up
  - Ensure that you are in the root folder (sentinel/)

  Run `python -m uvicorn data_sources.api:app --reload`
  - This command will boot up the backend

  
  Frontend:
  - Open another new terminal for the frontend to boot up
  
  Run cd frontend
  - This command will switch to the frontend folder

  Run `npm run dev`
  - This command will boot up the frontend
  - Copy and paste or Ctrl + click the link into the browser/VSCode