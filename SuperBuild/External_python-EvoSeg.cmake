set(proj python-EvoSeg)

# Set dependency list
set(${proj}_DEPENDENCIES
  python-scipy
  python-numpy
  )

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj DEPENDS_VAR ${proj}_DEPENDENCIES)
  
set(requirements_file ${CMAKE_BINARY_DIR}/${proj}-requirements.txt)
file(WRITE ${requirements_file} [===[
# [torch]
torch==2.4.0 --hash=sha256:0da13570771e09f6d754196aa865a690222d683df07b62f20922a3f27546faf5  \
             --hash=sha256:e0a73c7384d3e0a09fea5c2a10afc95bac9386e7360fe0bddd167b09697f59a8 
torchvision==0.19.0  --hash=sha256:03fc97a9058bb489aee898d2b7cef7e2e7636ecda1d9afbadf03e5b7268ae07a \
                     --hash=sha256:1f595eae367fbe7a46ec85fe6c55fa4185ef8b31bde5ae9b018c6b615b09c7d7
light-the-torch==0.5  --hash=sha256:a5ba9c1ed1e6efe28469d0759d603ddffdaecab0d545296aaff180116f694884
# [/torch]
# [fire]
fire==0.6.0 --hash=sha256:54ec5b996ecdd3c0309c800324a0703d6da512241bc73b553db959d98de0aa66
# [/fire]
# [SimpleITK]
SimpleITK==2.3.1 --hash=sha256:aec45af0ec031ed2a18f4dc8e2a12188817c789ea1db0a2c863506dce9ae2b87
# [/SimpleITK]
# [nibabel]
nibabel==5.3.2 --hash=sha256:52970a5a8a53b1b55249cba4d9bcfaa8cc57e3e5af35a29d7352237e8680a6f8
importlib_resources==6.4.5 --hash=sha256:ac29d5f956f01d5e4bb63102a5a19957f1b9175e45649977264a1416783bb717
zipp==3.20.2 --hash=sha256:a817ac80d6cf4b23bf7f2828b7cabf326f15a001bea8b1f9b49631780ba28350
# [/nibabel]
# [scikit-image]
scikit-image==0.24.0 --hash=sha256:56dab751d20b25d5d3985e95c9b4e975f55573554bd76b0aedf5875217c93e69
lazy_loader==0.4 --hash=sha256:342aa8e14d543a154047afb4ba8ef17f5563baad3fc610d7b15b213b0f119efc
imageio==2.36.0 --hash=sha256:471f1eda55618ee44a3c9960911c35e647d9284c68f077e868df633398f137f0
tifffile==2024.8.30 --hash=sha256:8bc59a8f02a2665cd50a910ec64961c5373bee0b8850ec89d3b7b485bf7be7ad
# [/scikit-image]
# [jinja2]
jinja2==3.1.4 --hash=sha256:bc5dd2abb727a5319567b7a813e6a2e7318c39f4f487cfe6c89c6f9c7d25197d
MarkupSafe==3.0.2 --hash=sha256:6e296a513ca3d94054c2c881cc913116e90fd030ad1c656b3869762b754f5f8a
# [/jinja2]
# [sympy]
sympy==1.13.3 --hash=sha256:54612cf55a62755ee71824ce692986f23c88ffa77207b30c1368eda4a7060f73
mpmath==1.3.0 --hash=sha256:a0b2b9fe80bbcd81a6647ff13108738cfb482d481d826cc0e02f5b35e5c88d2c
# [/sympy]
# [networkx]
networkx==3.2.1 --hash=sha256:f18c69adc97877c42332c170849c96cefa91881c99a7cb3e95b7c659ebdc1ec2
# [/networkx]
# [filelock]
filelock==3.16.1 --hash=sha256:2082e5703d51fbf98ea75855d9d5527e33d8ff23099bec374a134febee6946b0
# [/filelock]

# [typing-extensions]
typing-extensions==4.8.0 --hash=sha256:8f92fc8806f9a6b641eaa5318da32b44d401efaac0f6678c9bc448ba3605faa0
# [/typing-extensions]

# [fsspec]
fsspec==2024.10.0 --hash=sha256:03b9a6785766a4de40368b88906366755e2819e758b83705c88cd7cb5fe81871
# [/fsspec]

#[pillow]
pillow==11.0.0 --hash=sha256:94f3e1780abb45062287b4614a5bc0874519c86a777d4a7ad34978e86428b8dd
#[/pillow]

packaging==24.1 --hash=sha256:5b8f2217dbdbd2f7f384c41c628544e6d52f2d0f53c6d0c3ea61aa5d1d7ff124
]===])

ExternalProject_Add(${proj}
  ${${proj}_EP_ARGS}
  DOWNLOAD_COMMAND ""
  SOURCE_DIR ${CMAKE_BINARY_DIR}/${proj}
  BUILD_IN_SOURCE 1
  CONFIGURE_COMMAND ""
  BUILD_COMMAND ""
  INSTALL_COMMAND ${PYTHON_EXECUTABLE} -m pip install --extra-index-url https://download.pytorch.org/whl/cu118 -r ${requirements_file}
  LOG_INSTALL 1
  DEPENDS
    ${${proj}_DEPENDENCIES}
  )
  list(APPEND Slicer_DEPENDENCIES ${proj})