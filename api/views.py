# from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import connections
from collections import namedtuple
from rest_framework.decorators import api_view
from rest_framework.decorators import parser_classes
from rest_framework.parsers import JSONParser
import json
from rest_framework.response import Response
from rest_framework import status
from toscaparser.tosca_template import ToscaTemplate
import random
from django.views.decorators.csrf import csrf_exempt
def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def index(request):
    cursor = connections['nfv'].cursor()
    sql = "SELECT User_Id, User_Type,First_Name FROM VNF_User"
    print 'sql:' + sql
    cursor.execute(sql)
    results = namedtuplefetchall(cursor)

    for row in results:
        print "User Id " + str(row.User_Id)
        print "User Type " + str(row.User_Type)
        row = cursor.fetchone()
    # print results[0][0]
    # print results[0].User_Id

    # data = cursor.fetchall()
    # for row in data :
    #     print row[0].User_Id
    #     row = cursor.fetchone()

    cursor.close()
    return HttpResponse("Hi... Neo is back...")


def login(request):
    return HttpResponse("Hello Login API...")


@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def loginHandler(request, userId='Ben', pwd=''):
    print 'userId:' + userId
    print 'pwd:' + pwd
    cursor = connections['nfv'].cursor()
    if request.method == 'GET':
        sql = "SELECT User_Type FROM VNF_User where User_Id='" + userId + "' and Password='" + pwd + "'"
        print 'sql:' + sql
        cursor.execute(sql)
        results = namedtuplefetchall(cursor)
        for row in results:
            userRole = str(row.User_Type)
            print "User Type " + userRole
            return JsonResponse({'UserRole': userRole, 'UserId': userId})
        return JsonResponse({'UserRole': '', 'UserId': userId})
            # elif request.method == 'POST':
            #     #return HttpResponse("Hello Login API post call response...")
            #     return Response({'received data': request.data})

#
# class loginHandler (views.APIView) :
#     def get(self, request, *args, **kwargs):
#         username = kwargs['username']
#         print 'Logged In User:'+username
#         return HttpResponse(username)


@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def approveCatalog(request, catalogId=''):
    d = json.loads(catalogId)
    for id in d:
        updateCatalog(id, "A")
    return JsonResponse({'status': 'success', 'catalogId': catalogId})

@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def rejectCatalog(request, catalogId=''):
    d = json.loads(catalogId)
    for id in d:
        updateCatalog(id, "R")
    return JsonResponse({'status': 'success', 'catalogId': catalogId})

@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def deleteCatalog(request, catalogId=''):
    cursor = connections['nfv'].cursor()
    sql = "delete from vnf_catalog where catalog_Id="+catalogId
    print 'sql:' + sql
    cursor.execute(sql)
    return JsonResponse({'status': 'deleted', 'catalogId': catalogId})

@csrf_exempt
def toscaValidate(request):
    path = handle_uploaded_file(request.FILES['path'])
    print 'here'
    #path = request.GET.get('path', '')
    obj = ToscaTemplate(path, None, True)
    print obj.msg
    if obj.msg == 'success':
        return JsonResponse({'status': 'success', 'message': 'TOSCA Validation Successful', 'path' : path})
    else:
        return JsonResponse({'status': 'failed', 'message': obj.msg})

@csrf_exempt
def uploadImage(request):
    path = handle_uploaded_file(request.FILES['path'])
    return JsonResponse({'status': 'success', 'path': path})

def handle_uploaded_file(f):
    print f.name
    extension = f.name.split('.')[-1]
    filename = f.name +`random.random()` + '.' + extension
    path = 'C:\\'+ filename
    with open(path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return path

def updateCatalog(catalogId, status):
    cursor = connections['nfv'].cursor()
    sql = "update vnf_catalog set status = '" + status + "' where catalog_Id=" + str(catalogId) + ""
    print 'sql:' + sql
    cursor.execute(sql)
    return JsonResponse({'status': 'success', 'catalogId': catalogId})

@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def create_vnf_catalog(request, catalogName, vmImageFile, vnfdFilename, catalogDesc='', vnfdCfgFilename='',
                       vnfdParamFilename='', vnfdFilePath='',vnfdCfgFilePath='', vnfdParamPath='', vmImagePath=''):
    print '\n' + 'Inside Create VNF Catalog...'
    print 'catalogName:' + catalogName
    print 'catalogDesc:' + catalogDesc
    print 'vmImageFile:' + vmImageFile
    print 'vnfdFilename:' + vnfdFilename
    print 'vnfdCfgFilename:' + vnfdCfgFilename
    print 'vnfdParamFilename:' + vnfdParamFilename

    cursor = connections['nfv'].cursor()
    status = 'P'
    if request.method == 'GET':
        sql = "INSERT INTO VNF_Catalog(Catalog_Name, Catalog_Desc,VM_Imagefile, VNFD_Filename, VNF_Config_Filename , VNF_Param_Filename, Status, VNFD_Path, VNF_Config_Path, VNF_Param_Path, VM_Image_Path) " + "VALUES ('" + catalogName + "','" + catalogDesc + "','" + vmImageFile + "','" + vnfdFilename + "','" + vnfdCfgFilename + "','" + vnfdParamFilename + "','" + status + "' ,'" + vnfdFilePath + "','" + vnfdCfgFilePath + "','" + vnfdParamPath + "','" + vmImagePath + "')"
        print 'sql:' + sql
        cursor.execute(sql)

        # Query to fetch Catalog_Id to the user
        retrieveSql = "SELECT Catalog_Id FROM VNF_Catalog where Catalog_Name='" + catalogName + "'";
        cursor.execute(retrieveSql)

        results = namedtuplefetchall(cursor)

        for row in results:
            catalogId = str(row.Catalog_Id)
            print "Catalog Id: " + catalogId
            return JsonResponse({'CatalogId': catalogId})


@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def list_vnf_catalog(request):
    print 'Inside VNF Catalog...'

    cursor = connections['nfv'].cursor()
    if request.method == 'GET':
        sql = "SELECT Catalog_Id, Catalog_Name, Catalog_Desc, VM_ImageFile, VNFD_Filename, VNF_Config_Filename , VNF_Param_Filename FROM VNF_Catalog where Status='P'"
        cursor.execute(sql)

        results = namedtuplefetchall(cursor)

        json_res = []

        for row in results:
            catalog_id = str(row.Catalog_Id)
            catalog_name = str(row.Catalog_Name)
            catalog_Desc = str(row.Catalog_Desc)
            vm_image_file = str(row.VM_ImageFile)
            vnfd_filename = str(row.VNFD_Filename)
            vnf_cfg_filename = str(row.VNF_Config_Filename)
            vnf_param_filename = str(row.VNF_Param_Filename)

            jsonobj = {'CatalogId': catalog_id, 'CatalogName': catalog_name, 'CatalogDesc': catalog_Desc,
                                'VM_ImageFile': vm_image_file, 'VNFD_Filename': vnfd_filename,
                                'VNF_Config_Filename': vnf_cfg_filename, 'VNF_Param_Filename': vnf_param_filename}

            #dataobj=[catalog_name,catalog_Desc,vm_image_file,vnfd_filename,vnf_cfg_filename,vnf_param_filename,catalog_id]

            json_res.append(jsonobj)
            #dataobj_res.append(dataobj)

    print 'JsonResponse:'+str(json_res)
    return JsonResponse(json_res, safe=False)