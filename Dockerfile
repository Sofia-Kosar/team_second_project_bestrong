#Build
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /app


RUN dotnet tool install --global dotnet-ef --version 8.0.2
ENV PATH="$PATH:/root/.dotnet/tools"

COPY *.sln .
COPY DotNetCrudWebApi/*.csproj DotNetCrudWebApi/
RUN dotnet restore


COPY . .

RUN dotnet ef migrations bundle \
    --project DotNetCrudWebApi/DotNetCrudWebApi.csproj \
    -o /out/efbundle

RUN dotnet publish DotNetCrudWebApi/DotNetCrudWebApi.csproj \
    -c Release \
    -o /out

#Runtime
FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app

ENV ASPNETCORE_HTTP_PORTS=5000
EXPOSE 5000

COPY --from=build /out .

RUN mkdir -p /app/Data && chmod 777 /app/Data

ENTRYPOINT ["/bin/sh", "-c", "./efbundle && dotnet DotNetCrudWebApi.dll"]