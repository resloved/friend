FROM public.ecr.aws/lambda/python:3.8

RUN yum -y install \
    git \
    tar \
    unzip \
    make \
    gcc-c++

RUN curl -L https://cmake.org/files/v3.12/cmake-3.12.0.tar.gz > cmake-3.12.0.tar.gz
RUN tar xvzf cmake-3.12.0.tar.gz
WORKDIR cmake-3.12.0
RUN ./bootstrap
RUN make
RUN make install
WORKDIR ../

RUN git clone --recursive https://github.com/saharNooby/rwkv.cpp rwkv
WORKDIR rwkv

RUN cmake -DBUILD_SHARED_LIBS=ON .
RUN cmake --build . --config Release

RUN pip install -r rwkv/requirements.txt

COPY friend-3B-Q4-0.bin release.bin
COPY app.py ../

ENV PYTHONUNBUFFERED 1

# Set the CMD to your handler
CMD ["app.lambda_handler"]
