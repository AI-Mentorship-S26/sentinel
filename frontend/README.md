
  # US Ports Dashboard

  This is a code bundle for US Ports Dashboard. The original project is available at https://www.figma.com/design/oO3slPymTSrNEAC8kAB8d2/US-Ports-Dashboard.


  Download Node.js and add to PATH
  Check npm -v

  Run 'pip install npm' (maybe unecessary)


  ## Setup
  Run `npm i` to install the dependencies.

  Run 'Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned' if scripts error appears
  

  ## To Run:

  Backend:
  cd data_sources

  Run `python -m uvicorn api:app --reload`

  
  Frontend:
  cd frontend

  Run `npm run dev`

  Copy and paste the http link into browser