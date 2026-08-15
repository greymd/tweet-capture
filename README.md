# x-post-capture

### Use existing image

```bash
$ docker run -it -v $PWD:/work --rm \
  ghcr.io/greymd/x-post-capture/x-post-capture:latest \
  https://x.com/username/status/123456789
$ ls
123456789_screenshot.png    # screenshot will be created on the current directory.
123456789_text.png          # text will be created on the current directory.
```

```bash
$ docker run -it -v $PWD:/work --rm \
  ghcr.io/greymd/x-post-capture/x-post-capture:latest \
  https://x.com/username/status/123456789 \
  --output-screenshot result.png \
  --output-text result.txt
$ ls
result.png    # screenshot will be created on the current directory.
result.txt    # text will be created on the current directory.
```

# For developers

### Build

```bash
$ docker build -t x-post-capture .
```

### Run

```bash
$ docker run -it -v $PWD:/work --rm x-post-capture https://x.com/username/status/123456789
```

### Push

```bash
$ docker tag x-post-capture ghcr.io/greymd/x-post-capture/x-post-capture:latest
$ docker push ghcr.io/greymd/x-post-capture/x-post-capture:latest
```

#### Push with finch (multi-platform build and push):

```bash
$ finch build \
  --platform linux/arm64,linux/amd64 \
  -t ghcr.io/greymd/x-post-capture/x-post-capture:latest \
  .

$ finch push \
  --all-platforms \
  ghcr.io/greymd/x-post-capture/x-post-capture:latest
```
