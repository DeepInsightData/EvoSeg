#-----------------------------------------------------------------------------
set(MODULE_NAME EvoSeg)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  ${MODULE_NAME}Lib/__init__.py
  ${MODULE_NAME}Lib/data.py
  ${MODULE_NAME}Lib/EvoSegModels.py
  ${MODULE_NAME}Lib/EvoSegSettingsPanel.py
  ${MODULE_NAME}Lib/nnunetv2_inference.py
  ${MODULE_NAME}Lib/post_process.py
  ${MODULE_NAME}Lib/resampling.py
  ${MODULE_NAME}Lib/modify_total_nnunet.py
  ${MODULE_NAME}Lib/modify_total_python_api.py
  ${MODULE_NAME}Lib/utils.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/Icons/EvoSeg_Cancel.png
  Resources/Icons/EvoSeg_Export.png
  Resources/Icons/EvoSeg_Model.png
  Resources/Icons/EvoSeg_Place.png
  Resources/Icons/artery_segmentation.png
  Resources/Icons/airway_segmentation.png
  Resources/Icons/lunglobe_segmentation.png
  Resources/Icons/rib_segmentation.png
  Resources/Icons/vein_segmentation.png
  Resources/Icons/nodule_segmentation.png
  Resources/UI/${MODULE_NAME}.ui
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
