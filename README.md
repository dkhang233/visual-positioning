# Visual Positioning System


## Client
Frontend for website. Use OpenLayer to create 2d map from json data
### How to run

* Install Nodejs

   * Download from [here](https://nodejs.org/en )

* Run script

    ```bash
    cd client
    npm install 
    npm run start
    ```



## Web Server
Handle request from client

### How to run 
* Run script

    ```bash
    cd web_server
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```


