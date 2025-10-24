# test_system.py
# 17 June 2025

from src.ms_system import MicroserviceSystem, Microservice, Endpoint, Repository, SystemConnectionGraph

def getTestMicroserviceSystem() -> MicroserviceSystem:
    # Roles
    systemRoles = {0b0001: "UnauthenticatedRole", 0b0010: "StudentRole", 0b0100: "TeacherRole", 0b1000: "AdminRole"}

    # Grades Service ===================================================================================================
    getGradesByStudentID = Endpoint([Repository(0b0100, "gradesRepository")],
                                    0b1110, "getGradesByStudentID")
    changeGradesByStudentID = Endpoint([Repository(0b1111, "gradesRepository")],
                                       0b1100,
                                       "changeGradesByStudentID")
    calculateGPA = Endpoint([Repository(0b0100, "gradesRepository")],
                            0b1110, "calculateGPA")
    gradesService = Microservice([getGradesByStudentID, changeGradesByStudentID,
                                  calculateGPA], "grades-service")

    # User Service =====================================================================================================
    getStudentsByTeacherID = Endpoint([Repository(0b0100, "userRepository")],
                                      0b1110,
                                      "getStudentsByTeacherID")
    addUser = Endpoint([Repository(0b1000, "userRepository")],
                       0b1000, "addUser")
    updateUser = Endpoint([Repository(0b0010, "userRepository")],
                          0b1110, "updateUser")
    deleteUser = Endpoint([Repository(0b0001, "userRepository")],
                          0b1000, "deleteUser")
    getUser = Endpoint([Repository(0b0100, "userRepository")],
                       0b1111, "getUser")
    login = Endpoint([Repository(0b0100, "userRepository")],
                     0b1111, "login")
    userService = Microservice([getStudentsByTeacherID, addUser, updateUser, deleteUser,
                                getUser, login], "user-service")

    # Course Delivery Service ==========================================================================================
    generateCourseReport = Endpoint([Repository(0b0100, "courseRepository")],
                                    0b1110,
                                    "generateCourseReport")
    exportGrades = Endpoint([Repository(0b1110, "courseRepository")],
                            0b1100, "exportGrades")
    addUserToCourse = Endpoint([Repository(0b0110, "courseRepository")],
                               0b1100, "addUserToCourse")
    removeUserFromCourse = Endpoint([Repository(0b0110, "courseRepository")],
                                    0b1100, "removeUserFromCourse")
    createCourse = Endpoint([Repository(0b1000, "courseRepository")],
                            0b1100, "createCourse")
    deleteCourse = Endpoint([Repository(0b0001, "courseRepository")],
                            0b1100, "deleteCourse")
    updateCourse = Endpoint([Repository(0b0010, "courseRepository")],
                            0b1100, "updateCourse")
    getCourse = Endpoint([Repository(0b0100, "courseRepository")],
                         0b1110, "getCourse")
    courseDeliveryService = Microservice([generateCourseReport, addUserToCourse, removeUserFromCourse,
                                          createCourse, deleteCourse, updateCourse, exportGrades,
                                          getCourse], "course-delivery-service")

    # File Storage Service =============================================================================================
    createFile = Endpoint([Repository(0b1000, "fileRepository")],
                          0b1110, "createFile")
    deleteFile = Endpoint([Repository(0b0001, "fileRepository")],
                          0b1110, "deleteFile")
    updateFile = Endpoint([Repository(0b0010, "fileRepository")],
                          0b1110, "updateFile")
    getFile = Endpoint([Repository(0b0100, "fileRepository")],
                       0b1111, "getFile")
    shareFile = Endpoint([Repository(0b0100, "fileRepository")],
                         0b1110, "shareFile")
    exportTranscript = Endpoint([Repository(0b0100, "fileRepository")],
                                0b1110, "exportTranscript")
    fileStorageService = Microservice([createFile, deleteFile, updateFile,
                                       getFile, shareFile, exportTranscript], "file-storage-service")

    # Admin Service ====================================================================================================
    pruneGraduatedStudents = Endpoint([Repository(0b1111, "adminRepository"),
                                       Repository(0b1111, "userRepository")],
                                      0b1000, "pruneGraduatedStudents")
    adminService = Microservice([pruneGraduatedStudents], "admin-service")

    # System Connections ===============================================================================================
    systemConnectionGraph = SystemConnectionGraph()
    systemConnectionGraph.addSystemConnection(getGradesByStudentID, getStudentsByTeacherID)
    systemConnectionGraph.addSystemConnection(changeGradesByStudentID, getStudentsByTeacherID)
    systemConnectionGraph.addSystemConnection(generateCourseReport, getGradesByStudentID)
    systemConnectionGraph.addSystemConnection(addUserToCourse, getUser)
    systemConnectionGraph.addSystemConnection(removeUserFromCourse, getUser)
    systemConnectionGraph.addSystemConnection(createCourse, getUser)
    systemConnectionGraph.addSystemConnection(getFile, getUser)
    systemConnectionGraph.addSystemConnection(deleteFile, getUser)
    systemConnectionGraph.addSystemConnection(updateFile, getUser)
    systemConnectionGraph.addSystemConnection(createFile, getUser)
    systemConnectionGraph.addSystemConnection(pruneGraduatedStudents, getFile)
    systemConnectionGraph.addSystemConnection(pruneGraduatedStudents, getUser)
    systemConnectionGraph.addSystemConnection(pruneGraduatedStudents, removeUserFromCourse)
    systemConnectionGraph.addSystemConnection(pruneGraduatedStudents, deleteFile)
    systemConnectionGraph.addSystemConnection(pruneGraduatedStudents, generateCourseReport)
    systemConnectionGraph.addSystemConnection(pruneGraduatedStudents, calculateGPA)
    systemConnectionGraph.addSystemConnection(pruneGraduatedStudents, getGradesByStudentID)
    systemConnectionGraph.addSystemConnection(exportGrades, changeGradesByStudentID)
    systemConnectionGraph.addSystemConnection(exportTranscript, getGradesByStudentID)

    # Microservice System ==============================================================================================
    educationDeliverySystem = MicroserviceSystem([gradesService, userService, courseDeliveryService,
                                                  fileStorageService, adminService],
                                                 systemConnectionGraph,
                                                 "education-delivery-system",
                                                 systemRoles)
    
    # Automated back-references
    educationDeliverySystem.populateBackReferences()

    return educationDeliverySystem