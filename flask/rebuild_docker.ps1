docker stop flask_container
docker rm flask_container
docker build -t flask_tfg .
docker run -d -p 5000:5000 --name flask_container flask_tfg