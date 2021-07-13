#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@文件     :traffic-flow-generator.py
@说明     : 读取自己的路网，并生成random flow, 支持指定生成车辆的类型
@时间     :2021/07/03 23:34:53
@作者     :TaoHong
@版本     :v2.3
'''


import os
import sumolib
import subprocess

# 保存所有类型车，自有的属性
vehicleParameters = {
    "passenger":  ["-p", "1.445465", "--vehicle-class", "passenger",  "--vclass", "passenger",  "--prefix", "veh",
                   "--min-distance", "300",  "--trip-attributes", 'departLane="best"',
                   "--fringe-start-attributes", 'departSpeed="max"',
                   "--allow-fringe.min-length", "1000",
                   "--lanes", "--validate"],
    "truck":      ["-p", "1.445465", "--vehicle-class", "truck", "--vclass", "truck", "--prefix", "truck", "--min-distance", "600",
                   "--fringe-start-attributes", 'departSpeed="max"',
                   "--trip-attributes", 'departLane="best"', "--validate"],
    "bus":        ["-p", "1.445465", "--vehicle-class", "bus",   "--vclass", "bus",   "--prefix", "bus",   "--min-distance", "600",
                   "--fringe-start-attributes", 'departSpeed="max"',
                   "--trip-attributes", 'departLane="best"', "--validate"],
    "motorcycle": ["-p", "1.445465", "--vehicle-class", "motorcycle", "--vclass", "motorcycle", "--prefix", "moto",
                   "--fringe-start-attributes", 'departSpeed="max"',
                   "--max-distance", "1200", "--trip-attributes", 'departLane="best"', "--validate"],
    "bicycle":    ["-p", "1.445465", "--vehicle-class", "bicycle",    "--vclass", "bicycle",    "--prefix", "bike",
                   "--fringe-start-attributes", 'departSpeed="max"',
                   "--max-distance", "8000", "--trip-attributes", 'departLane="best"', "--validate"],
    "tram":       ["-p", "1.445465", "--vehicle-class", "tram",       "--vclass", "tram",       "--prefix", "tram",
                   "--fringe-start-attributes", 'departSpeed="max"',
                   "--min-distance", "1200", "--trip-attributes",      'departLane="best"', "--validate"],
    "rail_urban": ["-p", "1.445465", "--vehicle-class", "rail_urban", "--vclass", "rail_urban", "--prefix", "urban",
                   "--fringe-start-attributes", 'departSpeed="max"',
                   "--min-distance", "1800", "--trip-attributes", 'departLane="best"', "--validate"],
    "rail":       ["-p", "1.445465", "--vehicle-class", "rail",       "--vclass", "rail",       "--prefix", "rail",
                   "--fringe-start-attributes", 'departSpeed="max"',
                   "--min-distance", "2400", "--trip-attributes",     'departLane="best"', "--validate"],
    "ship":       ["-p", "1.445465", "--vehicle-class", "ship",       "--vclass", "ship",       "--prefix", "ship", "--validate",
                   "--fringe-start-attributes", 'departSpeed="max"'],
    "pedestrian": ["-p", "1.445465", "--vehicle-class", "pedestrian", "--persontrips", "--prefix", "ped", 
                    "--additional-files", "osm_stops.add.xml,osm_pt22.rou.xml", "--trip-attributes", "modes=\"public\"" ],
    "persontrips": ["-p", "1.445465", "--vehicle-class", "pedestrian", "--persontrips", "--prefix", "ped",
                    "--trip-attributes", 'modes="public"'],
}



def add_filename(filenames, use, name):
    if use not in filenames.keys():
        filenames[use] = name
    else:
        print("use has been there!")
 

# 需要生成的车的类型（来自 vehicleParameters 的健值
vehicleNames = ["passenger", "bicycle", "pedestrian"]

# 重要文件存储（集中起来，方便修改
filenames={}
filenames["net"] = "osm.net.xml" #　需要读取路网文件的名称

filenames["stops"] = "osm_stops.add.xml" # 是public transport 交通量时，需要以下3个文件
filenames["ptlines"]= "osm_ptlines.xml"
filenames["ptroutes"]= "osm_pt22.rou.xml"

filenames["build.bat"] = "build22.bat" 
filenames["build.sh"] = "build22.sh"

filenames["config"]= "osm2.sumocfg"


additionalFiles=[]
additionalFiles.append("osm.poly.xml")
additionalFiles.append("osm_stops.add.xml")

# 根据 vehicleNames 生成对应的车的交通量定义文件
routeNames = {}
for vehicleType in vehicleNames:
    add_filename(routeNames, vehicleType, "osm22."+vehicleType+".trips.xml")

# 路网中所有车共有的属性，其实 -p 可以考虑每类车定义的一个的，但意义不大
options =[
            "-n", filenames["net"],
            "--fringe-factor", 4,
            "--seed", 42,
            "-e", 3600
        ]

# 是public transport 交通量的一些定义，和其他车不一样
ptOptions = [
                "-n", filenames["net"],
                "-o", filenames["ptroutes"],
                "-e", 3600,
                "-p", 600,
                "--random-begin",
                "--seed", 42,
                "--ptstops", filenames["stops"],
                "--ptlines", filenames["ptlines"],
                "--ignore-errors",
                "--vtype-prefix", "pt_",
                "--min-stops", 0,
                "--extend-to-fringe",
                "--verbose"
            ]



# 用来生成batch文件用的
def quoted_str(s):
    if type(s) == float:
        return "%.6f" % s
    elif type(s) != str:
        return str(s)
    elif '"' in s or ' ' in s:
        return '"' + s.replace('"', '\\"') + '"'
    else:
        return s


# 生成batch文件
def createBatch(filenames, vehicleNames, options, ptOptions):
    winbatchFile = filenames["build.bat"]
    macbatchFile = filenames["build.sh"]

    if os.name == "nt": 
        SUMO_HOME_VAR = "%SUMO_HOME%"
    else:
        SUMO_HOME_VAR = "$SUMO_HOME"
    
    # 调用 randomTrips.py 
    
    # 考虑mac和window的环境变量获取方式不一样，加了以下：   
    # nt =windows posix =linux
    if os.name =="nt": 
        SUMO_HOME_VAR = "%SUMO_HOME%"
        randomTripsPath = os.path.join(
                    SUMO_HOME_VAR, "tools", "randomTrips.py")
        # 调用 ptlines2flows.py
        ptlines2flowsPath = os.path.join(
                    SUMO_HOME_VAR, "tools", "ptlines2flows.py")
        with open(winbatchFile, 'w') as f:
            f.write("# !Windows\n")
            
            # 是public transport 交通量的命令行
            if ptOptions is not None:
                f.write('python "%s" %s\n' %
                        (ptlines2flowsPath, " ".join(map(quoted_str, ptOptions))))
                # 是一般车辆的交通量的命令行
                for vehicleType in vehicleNames:
                    output = options[:]
                    output.insert(4,"-o")
                    output.insert(5, routeNames[vehicleType])

                    if vehicleType == "pedestrian": 
                        output += ["-r", "osm22.pedestrian.rou.xml"]

                    f.write('python "%s" %s %s\n' %
                            (randomTripsPath,
                            " ".join(map(quoted_str, output)),
                            " ".join(map(quoted_str, vehicleParameters[vehicleType]))
                            )
                            )
    else:
        SUMO_HOME_VAR = "$SUMO_HOME"
        randomTripsPath = os.path.join(
                    SUMO_HOME_VAR, "tools", "randomTrips.py")
        # 调用 ptlines2flows.py
        ptlines2flowsPath = os.path.join(
                    SUMO_HOME_VAR, "tools", "ptlines2flows.py")
        with open(macbatchFile,'w') as f:
            f.write("# !MacOs\n")
            
            # 是public transport 交通量的命令行
            if ptOptions is not None:
                f.write('python "%s" %s\n' %
                        (ptlines2flowsPath, " ".join(map(quoted_str, ptOptions))))
            
            # 是一版车辆的交通量的命令行
            for vehicleType in vehicleNames:
                output = options[:]
                output.insert(2,"-o")
                output.insert(3, routeNames[vehicleType])


                f.write('python "%s" %s %s\n' %
                        (randomTripsPath,
                        " ".join(map(quoted_str, output)),
                        " ".join(map(quoted_str, vehicleParameters[vehicleType]))
                        )
                    )


# 生成.sumocfg文件
def makeConfigFile(filenames, routeNames):
    add_filename(filenames, "guisettings", "osm.view.xml")
    with open(filenames["guisettings"], 'w') as f:
        f.write("""
<viewsettings>
<scheme name="real world"/>
<delay value="20"/>
</viewsettings>
""")    
    
    sumo = sumolib.checkBinary("sumo")

    opts = [sumo, 
            "-n", filenames["net"], 
            "--gui-settings-file", filenames["guisettings"],
            "--duration-log.statistics",
            "--device.rerouting.adaptation-interval", "10",
            "--device.rerouting.adaptation-steps", "18",
            "-v", "--no-step-log", 
            "--save-configuration", filenames["config"], 
            "--ignore-route-errors"]

    if len(routeNames)>0:
        for outputfile in routeNames.keys(): # 替换一下行人的rou文件
            if outputfile == "pedestrian" :
                routeNames[outputfile]= "osm22.pedestrian.rou.xml"
        add_filename(routeNames,"ptroutes", filenames["ptroutes"])
        opts += ["-r", ", ".join(routeNames.values())]
        
    if len(additionalFiles) > 0:
        opts += ["-a", ",".join(additionalFiles)]
    subprocess.call(opts)



if __name__ == "__main__":
    print('helle, world!')
    createBatch(filenames, vehicleNames, options, ptOptions)
    makeConfigFile(filenames, routeNames)
    print('bye, world!')
    

