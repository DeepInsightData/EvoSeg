set(proj python-EvoSeg)

# Set dependency list
set(${proj}_DEPENDENCIES
  python-scipy
  python-numpy
  python-pythonqt-requirements
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
# [/torch]
# [fire]
fire==0.6.0 --hash=sha256:54ec5b996ecdd3c0309c800324a0703d6da512241bc73b553db959d98de0aa66
termcolor==2.5.0 --hash=sha256:37b17b5fc1e604945c2642c872a3764b5d547a48009871aea3edd3afa180afb8
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

# [nnunetv2]
nnunetv2==2.5.1 --hash=sha256:8dca9e6b49a443ad144774245340ada0c6fe84007930c3ba4c4467e12c510cdc
acvl_utils==0.2 --hash=sha256:d58636b5049b0ba698b6cbac27cdff9350458c40329555051083758c35e7da36
dynamic_network_architectures==0.3.1 --hash=sha256:e3702b451891c01ccdcbd468aea309ae7301ab706e27394a438f3edba3fd9acd
tqdm==4.66.6 --hash=sha256:223e8b5359c2efc4b30555531f09e9f2f3589bcd7fdd389271191031b49b7a63
dicom2nifti==2.5.0 --hash=sha256:9518dcc12a3d92c2415deca7dccf4606ec37b57dcecf716dbca53a7852efdaa5
batchgenerators==0.25 --hash=sha256:38a67413e847ff367e64abac36331fcb065494202d526ae96f7644de3a0e5495
scikit_learn==1.5.2 --hash=sha256:3bed4909ba187aca80580fe2ef370d9180dcf18e621a27c4cf2ef10d279a7efe
pandas==2.2.3 --hash=sha256:4850ba03528b6dd51d6c5d273c46f183f39a9baf3f0143e566b89450965b105e
graphviz==0.20.3 --hash=sha256:81f848f2904515d8cd359cc611faba817598d2feaac4027b266aa3eda7b3dde5
matplotlib==3.9.2 --hash=sha256:b2696efdc08648536efd4e1601b5fd491fd47f4db97a5fbfd175549a7365c1b2
seaborn==0.13.2 --hash=sha256:636f8336facf092165e27924f223d3c62ca560b1f2bb5dff7ab7fad265361987
imagecodecs==2024.9.22 --hash=sha256:3e55abc2934442fe3055b4f8943ebe8ff6c7eb57f9f895c80ca1732f38632d9f
yacs==0.1.8 --hash=sha256:99f893e30497a4b66842821bac316386f7bd5c4f47ad35c9073ef089aa33af32
batchgeneratorsv2==0.2.1 --hash=sha256:a681f7a81956ddba11f72aed20ae468b118166f9c950a61662f8ec422fea3cf1
einops==0.8.0 --hash=sha256:9572fb63046264a862693b0a87088af3bdc8c068fde03de63453cbbde245465f
connected_components_3d==3.19.0 --hash=sha256:4d294748c120e1255e8707b57857da1da75e8b99b28862103f7333572e65cf37
colorama==0.4.6 --hash=sha256:4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6
python_gdcm==3.0.24.1 --hash=sha256:988daae3828d35dc0ceaba8fb0c337b893991480dfff4c6dbdc6818b3d1b7db4
future==1.0.0 --hash=sha256:929292d34f5872e70396626ef385ec22355a1fae8ad29e1a734c3e43f9fbc216
unittest2==1.1.0 --hash=sha256:13f77d0875db6d9b435e1d4f41e74ad4cc2eb6e1d5c824996092b3430f088bb8
threadpoolctl==3.5.0 --hash=sha256:56c1e26c150397e58c4926da8eeee87533b1e32bef131bd4bf6a2f45f3185467
joblib==1.4.2 --hash=sha256:06d478d5674cbc267e7496a410ee875abd68e4340feff4490bcb7afb88060ae6
python_dateutil==2.9.0 --hash=sha256:cbf2f1da5e6083ac2fbfd4da39a25f34312230110440f424a14c7558bb85d82e
pytz==2024.2 --hash=sha256:31c7c1817eb7fae7ca4b8c7ee50c72f93aa2dd863de768e1ef4245d426aa0725
tzdata==2024.2 --hash=sha256:a48093786cdcde33cad18c2555e8532f34422074448fbc874186f0abd79565cd
contourpy==1.3.0 --hash=sha256:14e262f67bd7e6eb6880bc564dcda30b15e351a594657e55b7eec94b6ef72843
cycler==0.12.1 --hash=sha256:85cef7cff222d8644161529808465972e51340599459b8ac3ccbac5a854e0d30
fonttools==4.22.0 --hash=sha256:4ed7a4c1bba3b76aea0338184671ff091603c788d17b76d0aa0183c8b78b947c
kiwisolver==1.4.7 --hash=sha256:cf0438b42121a66a3a667de17e779330fc0f20b0d97d59d2f2121e182b0505e4
PyYAML==6.0.2 --hash=sha256:39693e1f8320ae4f43943590b49779ffb98acb81f788220ea932a6b6c51004d8
fft_conv_pytorch==1.2.0 --hash=sha256:17b9bd616df86da25e4820473698eb4831c2f2f6e73906961901e6c278098f3c
argparse==1.4.0 --hash=sha256:c31647edb69fd3d465a847ea3157d37bed1f95f19760b11a47aa91c04b666314
traceback2==1.4.0 --hash=sha256:8253cebec4b19094d67cc5ed5af99bf1dba1285292226e98a31929f87a5d6b23
linecache2==1.0.0 --hash=sha256:e78be9c0a0dfcbac712fe04fbf92b96cddae80b1b842f24248214c8496f006ef
# [/nnunetv2]
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