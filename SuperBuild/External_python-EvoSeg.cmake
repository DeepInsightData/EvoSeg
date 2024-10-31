set(proj python-EvoSeg)

# Set dependency list
set(${proj}_DEPENDENCIES
  python-scipy
  )

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj DEPENDS_VAR ${proj}_DEPENDENCIES)
  
set(requirements_file ${CMAKE_BINARY_DIR}/${proj}-requirements.txt)
file(WRITE ${requirements_file} [===[
# [fire]
fire==0.6.0
# [/fire]
# [SimpleITK]
SimpleITK==2.3.1
# [/SimpleITK]
# [torch]
--index-url https://download.pytorch.org/whl/cu118 torch==2.4.0
--index-url https://download.pytorch.org/whl/cu118 torchvision==0.19.0
# [/torch]
]===])

ExternalProject_Add(${proj}
  ${${proj}_EP_ARGS}
  DOWNLOAD_COMMAND ""
  SOURCE_DIR ${CMAKE_BINARY_DIR}/${proj}
  BUILD_IN_SOURCE 1
  CONFIGURE_COMMAND ""
  BUILD_COMMAND ""
  INSTALL_COMMAND ${PYTHON_EXECUTABLE} -m pip install -r ${requirements_file}
  LOG_INSTALL 1
  DEPENDS
    ${${proj}_DEPENDENCIES}
  )
  list(APPEND Slicer_DEPENDENCIES ${proj})