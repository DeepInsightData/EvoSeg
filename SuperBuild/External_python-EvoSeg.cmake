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
six==1.16.0 --hash=sha256:8abb2f1d86890a2dfb989f9a77cfcfd3e47c2a354b01111771326f8aa26e0254
# [/fire]
# [nibabel]
nibabel==5.3.2 --hash=sha256:52970a5a8a53b1b55249cba4d9bcfaa8cc57e3e5af35a29d7352237e8680a6f8
importlib_resources==6.4.5 --hash=sha256:ac29d5f956f01d5e4bb63102a5a19957f1b9175e45649977264a1416783bb717
zipp==3.20.2 --hash=sha256:a817ac80d6cf4b23bf7f2828b7cabf326f15a001bea8b1f9b49631780ba28350
numpy==1.26 --hash=sha256:020cdbee66ed46b671429c7265cf00d8ac91c046901c55684954c3958525dab2
packaging==24.2 --hash=sha256:09abb1bccd265c01f4a3aa3f7a7db064b36514d2cba19a2f694fe6150451a759
# [/nibabel]
# [scikit-image]
scikit-image==0.24.0 --hash=sha256:56dab751d20b25d5d3985e95c9b4e975f55573554bd76b0aedf5875217c93e69
lazy_loader==0.4 --hash=sha256:342aa8e14d543a154047afb4ba8ef17f5563baad3fc610d7b15b213b0f119efc
imageio==2.36.0 --hash=sha256:471f1eda55618ee44a3c9960911c35e647d9284c68f077e868df633398f137f0
tifffile==2024.8.30 --hash=sha256:8bc59a8f02a2665cd50a910ec64961c5373bee0b8850ec89d3b7b485bf7be7ad
scipy==1.13.1 --hash=sha256:392e4ec766654852c25ebad4f64e4e584cf19820b980bc04960bca0b0cd6eaa2
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
typing-extensions==4.12.1 --hash=sha256:6024b58b69089e5a89c347397254e35f1bf02a907728ec7fee9bf0fe837d203a
# [/typing-extensions]

# [fsspec]
fsspec==2024.10.0 --hash=sha256:03b9a6785766a4de40368b88906366755e2819e758b83705c88cd7cb5fe81871
# [/fsspec]

#[pillow]
pillow==10.3.0 --hash=sha256:0ba26351b137ca4e0db0342d5d00d2e355eb29372c05afd544ebf47c0956ffeb
#[/pillow]

# [nnunetv2]
nnunetv2==2.5.1 --hash=sha256:8dca9e6b49a443ad144774245340ada0c6fe84007930c3ba4c4467e12c510cdc
acvl_utils==0.2 --hash=sha256:d58636b5049b0ba698b6cbac27cdff9350458c40329555051083758c35e7da36
dynamic_network_architectures==0.3.1 --hash=sha256:e3702b451891c01ccdcbd468aea309ae7301ab706e27394a438f3edba3fd9acd
tqdm==4.67.1 --hash=sha256:26445eca388f82e72884e0d580d5464cd801a3ea01e63e5601bdff9ba6a48de2
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
python_dateutil==2.9.0.post0 --hash=sha256:a8b2bc7bffae282281c8140a97d3aa9c14da0b136dfe83f850eea9a5f7470427
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
requests==2.32.3 --hash=sha256:70761cfe03c773ceb22aa2f671b4757976145175cdfca038c02654d061d6dcc6
pydicom==2.4.4 --hash=sha256:f9f8e19b78525be57aa6384484298833e4d06ac1d6226c79459131ddb0bd7c42
pyparsing==3.1.2 --hash=sha256:f9db75911801ed778fe61bb643079ff86601aca99fcae6345aa67292038fb742
idna==3.7 --hash=sha256:82fee1fc78add43492d3a1898bfa6d8a904cc97d8427f683ed8e798d07761aa0
urllib3==2.3.0 --hash=sha256:1cee9ad369867bfdbbb48b7dd50374c0967a0bb7710050facf0dd6911440e3df
chardet==5.2.0 --hash=sha256:e1cf59446890a00105fe7b7912492ea04b6e6f06d4b742b2c788469e34c82970
certifi==2024.2.2 --hash=sha256:dc383c07b76109f368f6106eee2b593b04a011ea4d55f652c6ca24a754d1cdd1
charset_normalizer==3.3.2 --hash=sha256:b01b88d45a6fcb69667cd6d2f7a9aeb4bf53760d7fc536bf679ec94fe9f3ff3d
# [/nnunetv2]

# [pynrrd]
pynrrd==1.0.0 --hash=sha256:65e5a61920d2f01ecf321eb41b0472940e181e4ba5e8a32f01ef5499d4192db5
nptyping==2.5.0 --hash=sha256:764e51836faae33a7ae2e928af574cfb701355647accadcc89f2ad793630b7c8
# [/pynrrd]

# [psutil]
psutil==6.1.0 --hash=sha256:a8fb3752b491d246034fa4d279ff076501588ce8cbcdbb62c32fd7a377d996be
# [/psutil]

#[TotalSegmentator]
TotalSegmentator==2.4.0 --hash=sha256:41974e5d61958a679aead73890c72e0ec79f504e7cca0965d609f1ff11678fdc
p_tqdm==1.4.2 --hash=sha256:0f860c5facd0b0059da39998e55cfc035563f92d85d2f4895ba88a675c3c7529
xvfbwrapper==0.2.9 --hash=sha256:bcf4ae571941b40254faf7a73432dfc119ad21ce688f1fdec533067037ecfc24
pyarrow==18.1.0 --hash=sha256:a1880dd6772b685e803011a6b43a230c23b566859a6e0c9a276c1e0faf4f4052
pathos==0.2.5 --hash=sha256:21ae2cb1d5a76dcf57d5fe93ae8719c7339f467e246163650c08ccf35b87c846
dataclasses==0.6 --hash=sha256:454a69d788c7fda44efd71e259be79577822f5e3f53f029a22d08004e951dc9f
ppft==1.6.6.1 --hash=sha256:9e2173042edd5cc9c7bee0d7731873f17fcdce0e42e4b7ab68857d0de7b631fc
dill==0.3.2 --hash=sha256:6e12da0d8e49c220e8d6e97ee8882002e624f1160289ce85ec2cc0a5246b3a2e
pox==0.2.7 --hash=sha256:06afe1a4a1dbf8b47f7ad5a3c1d8ada9104c64933a1da11338269a2bd8642778
multiprocess==0.70.9 --hash=sha256:9fd5bd990132da77e73dec6e9613408602a4612e1d73caf2e2b813d2b61508e5
#[/TotalSegmentator]
]===])

ExternalProject_Add(${proj}
  ${${proj}_EP_ARGS}
  DOWNLOAD_COMMAND ""
  SOURCE_DIR ${CMAKE_BINARY_DIR}/${proj}
  BUILD_IN_SOURCE 1
  CONFIGURE_COMMAND ""
  BUILD_COMMAND ""
  INSTALL_COMMAND ${PYTHON_EXECUTABLE} -m pip install --no-deps --ignore-installed --extra-index-url https://download.pytorch.org/whl/cu118 -r ${requirements_file}
  LOG_INSTALL 1
  DEPENDS
    ${${proj}_DEPENDENCIES}
  )
  list(APPEND Slicer_DEPENDENCIES ${proj})