// Build FlatCG

package com.example.hello;

import java.io.File;
import java.util.*;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.io.FileWriter;

import soot.jimple.toolkits.callgraph.*;
import soot.jimple.toolkits.callgraph.CallGraph;
import soot.jimple.toolkits.callgraph.Edge;
import soot.*;
import soot.options.Options;
import soot.toolkits.graph.*;
import soot.util.*;
import soot.jimple.JimpleBody;
import soot.jimple.InvokeStmt;
import soot.jimple.internal.JAssignStmt;
import soot.jimple.InvokeExpr;
import java.lang.System;
import java.io.PrintWriter;

import java.util.regex.Pattern;
import java.util.regex.Matcher;

import soot.jimple.DynamicInvokeExpr;
import soot.jimple.InstanceInvokeExpr;
import soot.jimple.InterfaceInvokeExpr;
import soot.jimple.SpecialInvokeExpr;
import soot.jimple.StaticInvokeExpr;
import soot.jimple.VirtualInvokeExpr;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.serializer.SerializerFeature;

public class BuildMyCGRelease {

    public static Map<String, String> allFunctionDict = new HashMap<>();
    public static int allFunctionNumberIndex = -1;
    public static Set<String> dynamicInvokeFunctions = new HashSet<>();
    public static Set<String> instanceInvokeFunctions = new HashSet<>();
    public static Set<String> interfaceInvokeFunctions = new HashSet<>();
    public static Set<String> specialInvokeFunctions = new HashSet<>();
    public static Set<String> staticInvokeFunctions = new HashSet<>();
    public static Set<String> virtualInvokeFunctions = new HashSet<>();
    public static Set<String> allClassesInThisPackage = new HashSet<>();
    public static Set<String> crossPackageFunctions = new HashSet<>();
    public static Map<String, Set<String>> entranceAndReachableFunctions = new HashMap<>();

    public static void main(String[] args) {

        String inputFilePath = args[0];
        String outputFilePathRoot = args[1];
        String thisGAV = args.length >= 3 ? args[2] : "null"; 
        String thisPackageName = args.length >= 4 ? args[3] : "null";

        File file = new File(inputFilePath);
        String fileName = file.getName();

        String[] sootArgs = {
            "-pp",
            "-process-dir", inputFilePath,
            "-allow-phantom-refs",
            "-no-bodies-for-excluded", 
            "-whole-program",
            "-w",
            "-p", "cg.cha", "enabled:true",
            "-dynamic-dir", inputFilePath,
        };
        Options.v().parse(sootArgs);     
        Options.v().set_process_dir(Collections.singletonList(inputFilePath));
        Scene.v().loadNecessaryClasses();  
        Options.v().setPhaseOption("cg", "all-reachable:true");

        PackManager.v().getPack("wjtp").add(new Transform("wjtp.myTransform", new SceneTransformer() {
            @Override
            protected void internalTransform(String phaseName, Map<String, String> options) {
                
                // Build function dictionary
                for (SootClass sc : Scene.v().getClasses()) {
                    if (sc.isApplicationClass()){
                        allClassesInThisPackage.add(sc.getName());
                        for (SootMethod sm : sc.getMethods()){
                            addOrGetInallFunctionDict(sm);
                        }
                    } 
                }

                // Output json class
                PkgInfoJsonClass PkgInfo = new PkgInfoJsonClass();
                List<String> thisPackageNames = new ArrayList<>();
                if(!thisPackageName.equals("null")) thisPackageNames.add(thisPackageName);

                // Record each class's methods
                Map<String, List<String>> shortCG = new HashMap<String, List<String>>();

                // Find all public class
                Iterator<SootClass> classIterator = Scene.v().getClasses().iterator();
                while (classIterator.hasNext()) {
                    SootClass sootClass = classIterator.next();
                    if (sootClass.isApplicationClass() && sootClass.isPublic() && !isJavaLibClass(sootClass)) {

                        String pkgName = sootClass.getPackageName();
                        if (!thisPackageNames.contains(pkgName)) {
                            thisPackageNames.add(pkgName);
                        }

                        System.out.println("check class = " + sootClass.getName());
                        try{
                            List<String> clsMethods = new ArrayList<String>();

                            for (SootMethod sootMethod : sootClass.getMethods()) {
                                System.out.println("\t\tcheck method = " + sootMethod.getName());

                                // Find all non-private method
                                if (isNotJavaLibFuns(sootMethod) && (sootMethod.isPublic() || sootMethod.isProtected())) {
                                    clsMethods.add(sootMethod.getSignature());

                                    Set<String> thisEntranceReachableFunctions = new HashSet<>();

                                    // Get all reachable functions for this method
                                    //System.out.println("try get reachable for " + sootMethod.getSignature());
                                    Map<SootMethod, SootMethod> reachableMethodMap = getAllReachableMethodsNew(sootMethod);

                                    if (reachableMethodMap == null) {
                                        //System.out.println("no reachable");
                                    }
                                    else{
                                        for (Map.Entry<SootMethod, SootMethod> entry : reachableMethodMap.entrySet()) {
                                            //System.out.println("\t\t\tCheck Reachable = " + entry.getKey().getName());

                                            SootMethod mapKey = entry.getKey();
                                            SootMethod mapValue = entry.getValue();
                                            
                                            //if(mapValue!=null){
                                            if(isNotJavaLibFuns(mapKey) && mapValue!=null){
                                                // transfer to number
                                                thisEntranceReachableFunctions.add(addOrGetInallFunctionDict(mapKey));
                                            }
                                        }
                                    }
                                    entranceAndReachableFunctions.put(getInallFunctionDict(sootMethod),thisEntranceReachableFunctions);
                                }
                            }
                            shortCG.put(sootClass.getName(),clsMethods);
                        } catch(Exception e) {
                            System.out.println("entry funcs exception for class = " + sootClass.getName());
                        }
                    }
                }

                // Explicitly adds function calls from sub class to super class in the flat cg
                System.out.println("start add static call");
                classIterator = Scene.v().getClasses().iterator();
                while (classIterator.hasNext()) {
                    SootClass sootClass = classIterator.next();
                    String father_class = sootClass.getName();
                    if (shortCG.containsKey(father_class)){
                        List<String> father_functions = shortCG.get(father_class);

                        if(sootClass.isInterface()){
                            for (SootClass subinterface : Scene.v().getActiveHierarchy().getSubinterfacesOf(sootClass)) {
                                if (Scene.v().getLibraryClasses().contains(subinterface) || isJavaLibClass(subinterface))
                                    continue;
                                String subInterfaceName = subinterface.getName();
                                //some class may not exist in keys of shortCG, for example, some private classes. We do not need to care about them
                                if (shortCG.containsKey(subInterfaceName)){
                                    List<String> son_functions = shortCG.get(subInterfaceName);
                                    addInheritance(sootClass, father_functions, subinterface, son_functions);
                                }
                            }
                            for (SootClass subClass : Scene.v().getActiveHierarchy().getImplementersOf(sootClass)) {
                                if (Scene.v().getLibraryClasses().contains(subClass) || isJavaLibClass(subClass))
                                    continue;
                                String subClassName = subClass.getName();
                                if (shortCG.containsKey(subClassName)){
                                    List<String> son_functions = shortCG.get(subClassName);
                                    addInheritance(sootClass, father_functions, subClass, son_functions);
                                }
                            }
                        }
                        else{
                            for (SootClass subClass : Scene.v().getActiveHierarchy().getSubclassesOf(sootClass)) {
                                if (Scene.v().getLibraryClasses().contains(subClass) || isJavaLibClass(subClass))
                                    continue;
                                String subClassName = subClass.getName();
                                if (shortCG.containsKey(subClassName)){
                                    List<String> son_functions = shortCG.get(subClassName);
                                    addInheritance(sootClass, father_functions, subClass, son_functions);
                                }
                            }
                        }
                    }
                }

                // Assemble result
                PkgInfo.setDynamicInvokeFunctions(dynamicInvokeFunctions);
                PkgInfo.setInstanceInvokeFunctions(instanceInvokeFunctions);
                PkgInfo.setInterfaceInvokeFunctions(interfaceInvokeFunctions);
                PkgInfo.setSpecialInvokeFunctions(specialInvokeFunctions);
                PkgInfo.setStaticInvokeFunctions(staticInvokeFunctions);
                PkgInfo.setVirtualInvokeFunctions(virtualInvokeFunctions);
                PkgInfo.setCrossPackageFunctions(crossPackageFunctions);
                PkgInfo.setEntranceAndReachableFunctions(entranceAndReachableFunctions);
                PkgInfo.setGAV(thisGAV);
                PkgInfo.setPackageName(thisPackageNames);

                // Output result
                System.out.println("ready to output");
                PkgInfo.setAllFunctionDict(allFunctionDict);
                String jsonData = JSON.toJSONString(PkgInfo, SerializerFeature.PrettyFormat);
                System.out.println("Json Done");
                writeJson2File(jsonData, outputFilePathRoot+fileName.substring(0, fileName.lastIndexOf(".")) +"-PkgInfo.json");
                System.out.println("Success Gen PkgInfo " + fileName.substring(0, fileName.lastIndexOf(".")) +"-PkgInfo.json");
                System.out.println("Output Done");
  
            }
        }));

        PackManager.v().runPacks();
        //PackManager.v().writeOutput();

    }

    // For a given function, find all reachable functions, including directly reachable and indirectly reachable
    public static Map<SootMethod, SootMethod> getAllReachableMethodsNew(SootMethod initialMethod){
        
        CallGraph callgraph = Scene.v().getCallGraph();
        List<SootMethod> queue = new ArrayList<>();
        queue.add(initialMethod);
        //caller is value，callee is key. This works for our project
        Map<SootMethod, SootMethod> parentMap = new HashMap<>();  
        parentMap.put(initialMethod, null);

        // BFS algorithm
        for(int i=0; i< queue.size(); i++){
            SootMethod method = queue.get(i);

            for (Iterator<Edge> it = callgraph.edgesOutOf(method); it.hasNext(); ) {
                Edge edge = it.next();
                SootMethod childMethod = edge.tgt();
                SootMethod thisSrcMethod = edge.src();

                if(isNotJavaLibFuns(childMethod)){
                    try{
                        add2CallTypeRecord(getCallType(edge.srcStmt().getInvokeExpr()), addOrGetInallFunctionDict(childMethod));
                        if(!allClassesInThisPackage.contains(childMethod.getDeclaringClass().getName())){
                            crossPackageFunctions.add(addOrGetInallFunctionDict(childMethod));
                        }
                    }
                    catch (Exception e)  {
                        //System.out.println("exception" + childMethod);
                    }
                }
                //System.out.println(childMethod.getDeclaringClass().getPackageName());

                if(parentMap.containsKey(childMethod))
                    continue;

                parentMap.put(childMethod, method);
                queue.add(childMethod);
            }

            if(isNotJavaLibFuns(method)){
                //System.out.println("**********ow check valid method = " + method.getDeclaringClass().getName() + "." + method.getName());
                if(method.getDeclaringClass().isPhantomClass()){ 
                    //System.out.println(method.getDeclaringClass().getName() + " is PhantomClass");
                    String ClsName = method.getDeclaringClass().getName();
                    for(SootClass sootClass: Scene.v().getClasses()){
                        //if(sootClass.isApplicationClass()){
                            //System.out.println("travel " + sootClass.getName());
                        //}
                    }
                }
                else{
                    try {
                        JimpleBody body = (JimpleBody) method.retrieveActiveBody();
                        for (Unit unit : body.getUnits()){
                            if(unit instanceof JAssignStmt){
                                //System.out.println("This is assign");
                                Value rightOp = ((JAssignStmt) unit).getRightOp();
                                if(rightOp instanceof InvokeExpr){
                                    InvokeExpr InvokeExpr = (InvokeExpr) rightOp;
                                    SootMethod childMethod = InvokeExpr.getMethod();
                                    //System.out.println("[This Assign is Right InvokeExpr] " + InvokeExpr.getMethod());
                                    //System.out.println("above " + getCallType(InvokeExpr));
                                    if(parentMap.containsKey(childMethod))
                                        continue;
                                    parentMap.put(childMethod, method);
                                    queue.add(childMethod);

                                    if(isNotJavaLibFuns(childMethod)){
                                        add2CallTypeRecord(getCallType(InvokeExpr), addOrGetInallFunctionDict(childMethod));
                                        if(!allClassesInThisPackage.contains(childMethod.getDeclaringClass().getName())){
                                            crossPackageFunctions.add(addOrGetInallFunctionDict(childMethod));
                                        }
                                    }
                                }
                                else{
                                    //System.out.println("[This Assign is NOT Right InvokeExpr] ");
                                }
                            }
                            else if(unit instanceof InvokeStmt){
                                InvokeStmt invokeStmt = (InvokeStmt) unit;
                                //System.out.println("[InvokeExpr] " + invokeStmt.getInvokeExpr().getMethod());
                                //System.out.println("above" + getCallType(invokeStmt.getInvokeExpr()));
                                SootMethod childMethod = invokeStmt.getInvokeExpr().getMethod();
                                if(parentMap.containsKey(childMethod))
                                    continue;
                                parentMap.put(childMethod, method);
                                queue.add(childMethod);

                                if(isNotJavaLibFuns(childMethod)){
                                    add2CallTypeRecord(getCallType(invokeStmt.getInvokeExpr()), addOrGetInallFunctionDict(childMethod));
                                    if(!allClassesInThisPackage.contains(childMethod.getDeclaringClass().getName())){
                                        crossPackageFunctions.add(addOrGetInallFunctionDict(childMethod));
                                    }                                
                                }
                            }
                        }
                    } catch (Exception e)  {
                        //System.out.println("Error analyzing method: " + method.getSignature());
                        //e.printStackTrace();
                        try{
                            if(Modifier.isAbstract(method.getModifiers())){
                                SootClass currentClass = method.getDeclaringClass();
                                for (SootClass subClass : Scene.v().getActiveHierarchy().getSubclassesOf(currentClass)) {
                                    if (subClass.declaresMethod(method.getSubSignature())) {
                                        SootMethod implMethod = subClass.getMethod(method.getSubSignature());
                                    }
                                }
                            }
                        } catch (Exception ee)  {
                            //ee.printStackTrace();
                        }
                    }      
                }
            }
            else{
                //System.out.println("isNotJavaLibFuns " + method.getName());
            }
        }
        return parentMap;
    }

    public static boolean isJavaLibClass(SootClass sootClass){
        String name = sootClass.getName();
        if(name.startsWith("java")) 
            return true;
        if(name.startsWith("javax")) 
            return true;
        if(name.startsWith("sun.reflect.Reflection")) 
            return true;
        return false;
    }

    public static boolean isNotJavaLibFuns(SootMethod sootMethod){
        if(isJavaLibClass(sootMethod.getDeclaringClass())){
            return false;
        }
        return true;
    }

    public static void writeJson2File(String json, String outputFilePath){
        try {
            FileWriter writer = new FileWriter(outputFilePath);
            writer.write(json);
            writer.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static String getNewFileName(String fileName, int counter) {
        int dotIndex = fileName.lastIndexOf(".");
        if (dotIndex != -1) {
            return fileName.substring(0, dotIndex) + "_" + counter + fileName.substring(dotIndex);
        } else {
            return fileName + "_" + counter;
        }
    }

    public static String getCallType(InvokeExpr invokeExpr){
            if (invokeExpr instanceof InstanceInvokeExpr) {  
                return "Instance";  
            } else if (invokeExpr instanceof StaticInvokeExpr) {  
                return "Static";  
            } else if (invokeExpr instanceof VirtualInvokeExpr) {  
                return "Virtual";  
            } else if (invokeExpr instanceof InterfaceInvokeExpr) {  
                return "Interface";  
            } else if (invokeExpr instanceof SpecialInvokeExpr) {  
                return "Special";  
            } else if (invokeExpr instanceof DynamicInvokeExpr) {  
                return "Dynamic";  
            } 
            return "Unknown";
    }

    public static String addOrGetInallFunctionDict(SootMethod thisMethod){
        String method_signature = thisMethod.getSignature();
        if(allFunctionDict.containsKey(method_signature)){
            return allFunctionDict.get(method_signature);
        }
        else{
            allFunctionNumberIndex++;
            allFunctionDict.put(method_signature, Integer.toString(allFunctionNumberIndex));
            //System.out.println("》add2allFunctionDict: " + Integer.toString(allFunctionNumberIndex) + " " +method_signature);
            return Integer.toString(allFunctionNumberIndex);
        }
    }

    public static String addOrGetInallFunctionDict(String thisMethodSignature){
        if(allFunctionDict.containsKey(thisMethodSignature)){
            return allFunctionDict.get(thisMethodSignature);
        }
        else{
            allFunctionNumberIndex++;
            allFunctionDict.put(thisMethodSignature, Integer.toString(allFunctionNumberIndex));
            //System.out.println("》add2allFunctionDict: " + Integer.toString(allFunctionNumberIndex) + " " +thisMethodSignature);   
            return Integer.toString(allFunctionNumberIndex);
        }
    }

    public static String getInallFunctionDict(SootMethod thisMethod){
        return allFunctionDict.get(thisMethod.getSignature());
    }

    public static String getInallFunctionDict(String thisMethodSignature){
        return allFunctionDict.get(thisMethodSignature);
    }

    public static void add2CallTypeRecord(String callType, String functionNumber){
        switch(callType){
            case "Dynamic":
                dynamicInvokeFunctions.add(functionNumber);
                break;
            case "Instance":
                instanceInvokeFunctions.add(functionNumber);
                break;
            case "Interface":
                interfaceInvokeFunctions.add(functionNumber);
                break;
            case "Special":
                specialInvokeFunctions.add(functionNumber);
                break;
            case "Static":
                staticInvokeFunctions.add(functionNumber);
                break;
            case "Virtual":
                virtualInvokeFunctions.add(functionNumber);
                break;
        }
    }

    public static void addInheritance(SootClass fatherClass, List<String> father_functions, SootClass sonClass, List<String> son_functions){
        //System.out.println("to add in super class" + fatherClass.getName() + " subclass" + sonClass.getName());

        for (String father_function : father_functions) {
            String expected_son_function = father_function.replaceFirst(
                Pattern.quote(fatherClass.getName()),
                Matcher.quoteReplacement(sonClass.getName())
            );
            if (!son_functions.contains(expected_son_function)){
                //System.out.println("not find expected function" + expected_son_function);
                String entranceNumber = addOrGetInallFunctionDict(expected_son_function);
                //be care of putting a ref rather than a copy
                Set<String> thisEntranceReachableFunctions = new HashSet<>(entranceAndReachableFunctions.get(getInallFunctionDict(father_function)));
                thisEntranceReachableFunctions.add(getInallFunctionDict(father_function));

                entranceAndReachableFunctions.put(entranceNumber, thisEntranceReachableFunctions);
            }
        }
    }
}