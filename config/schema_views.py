from drf_spectacular.views import SpectacularYAMLAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


class SpectacularAPIView(SpectacularYAMLAPIView):
    title = 'gitDM API'
    description = 'gitDM API Documentation'
    version = '1.0.0'
    serve_include_schema = False
    schema_format = 'openapi-yaml'

# Optionally, you can add a simple endpoint to serve the schema as YAML
class OpenAPISchemaYAMLView(APIView):
    permission_classes = [AllowAny]  # noqa: RUF012

    def get(self, request, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN201
        view = SpectacularAPIView.as_view()
        return view(request, *args, **kwargs)
