from fastapi import FastAPI, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from ray import serve
from ray.serve.handle import DeploymentHandle
from localize_handler import LocalizeHandler
from image_retrival_deployment import ImageRetrival
from features_extractor_deployment import FeaturesExtractor
from features_matcher_deployment import FeaturesMatcher




app = FastAPI()

@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.5, "num_gpus": 0})
@serve.ingress(app)
class Ingress:
    def __init__(self, localize_handler: DeploymentHandle):
        self.localize_handler = localize_handler
        

    @app.post("/localize")
    async def localize(self, image: UploadFile) -> JSONResponse:
       ret = await self.localize_handler.localize.remote(image)
       return JSONResponse(content=ret, status_code=200)
        
       
hloc = Ingress.bind(LocalizeHandler.bind(FeaturesExtractor.bind(), ImageRetrival.bind(), FeaturesMatcher.bind()))
