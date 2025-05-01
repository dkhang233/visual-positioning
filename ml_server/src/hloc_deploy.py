from fastapi import FastAPI, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from ray import serve
from ray.serve.handle import DeploymentHandle
from localize_handler import LocalizeHandler
from image_retrival_deployment import ImageRetrival
from features_extractor_deployment import FeaturesExtractor
from features_matcher_deployment import FeaturesMatcher
from exception_handler import LocalizaionFailed
import time



app = FastAPI()

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 2, "num_gpus": 0})
@serve.ingress(app)
class Ingress:
    def __init__(self, localize_handler: DeploymentHandle):
        self.localize_handler = localize_handler
        

    @app.post("/localize")
    async def localize(self, image: UploadFile) -> JSONResponse:
        start_time = time.perf_counter()
        ret = await self.localize_handler.localize.remote(image)
        res = JSONResponse(content=ret, status_code=200)
        end_time = time.perf_counter()   
        print(f"Time taken for localize: {end_time - start_time} seconds")
        return res

    @app.post("/check")
    async def check(self, image: UploadFile) -> JSONResponse:
        ret = {
            "R": [
                -0.05414220400504355,
                0.5285674682215886,
                0.1037704144872635,
                0.8407834170346358
            ],
            "t": [
                -4.203817844215461,
                0.12726832016132747,
                -0.523618568089151
            ],
            "K": [
                [
                    1735.4910724468405,
                    0.0,
                    1920.0
                ],
                [
                    0.0,
                    1735.4910724468405,
                    1080.0
                ],
                [
                    0.0,
                    0.0,
                    1.0
                ]
            ]
        }
        return JSONResponse(content=ret, status_code=200)
        
       
hloc = Ingress.bind(LocalizeHandler.bind(FeaturesExtractor.bind(), ImageRetrival.bind(), FeaturesMatcher.bind()))
