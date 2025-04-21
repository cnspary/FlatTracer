// Build hierarchy info for call graph stitch

package com.example.hello;

import java.io.File;
import java.util.*;
import java.io.BufferedReader;
import java.io.BufferedWriter;
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

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.serializer.SerializerFeature;

public class BuildHierRelease {
    
    public static void main(String[] args) {

        String inputFilePath = args[0];
        String outputFilePath = args[1];
        
        File file = new File(inputFilePath);
        String fileName = file.getName();

        String[] sootArgs = {
            "-pp",
            "-process-dir", inputFilePath,
            "-allow-phantom-refs",
            "-no-bodies-for-excluded", 
            "-whole-program",
            "-w",
            "-verbose",
            "-dynamic-dir", inputFilePath,
        };
        Options.v().parse(sootArgs);
        Options.v().set_process_dir(Collections.singletonList(inputFilePath));
        Scene.v().loadNecessaryClasses();
        Options.v().setPhaseOption("cg", "all-reachable:true");
        Options.v().set_debug(true);

        PackManager.v().getPack("wjtp").add(new Transform("wjtp.myTransform", new SceneTransformer() {
            @Override
            protected void internalTransform(String phaseName, Map<String, String> options) {

                List<SootClass> classes = new ArrayList<>(Scene.v().getClasses());

                try {
                    FileWriter fileWriter = new FileWriter(outputFilePath);
                    BufferedWriter bufferedWriter = new BufferedWriter(fileWriter);

                    for (SootClass clazz : classes) {
                        if (isJavaLibClass(clazz))
                            continue;

                        String className = clazz.getName();
                        try{

                            if (Scene.v().getLibraryClasses().contains(clazz) || isJavaLibClass(clazz))
                                continue;

                            bufferedWriter.write("Class: " + className);
                            bufferedWriter.newLine();

                            // Each class is whether a interface or a class

                            if (clazz.isInterface()){ // if it is an interface
                                // Get all super interfaces
                                for (SootClass superinterface : Scene.v().getActiveHierarchy().getSuperinterfacesOf(clazz)) {
                                    if (Scene.v().getLibraryClasses().contains(superinterface) || isJavaLibClass(superinterface))
                                        continue;
                                    String superInterfaceName = superinterface.getName();
                                    bufferedWriter.write("  Superinterfaces: " + superInterfaceName);
                                    bufferedWriter.newLine();
                                }
                                // Get all sub interfaces
                                for (SootClass subinterface : Scene.v().getActiveHierarchy().getSubinterfacesOf(clazz)) {
                                    if (Scene.v().getLibraryClasses().contains(subinterface) || isJavaLibClass(subinterface))
                                        continue;
                                    String subInterfaceName = subinterface.getName();
                                    bufferedWriter.write("  Subinterfaces: " + subInterfaceName);
                                    bufferedWriter.newLine();
                                }
                                // Get all implementers
                                for (SootClass imp : Scene.v().getActiveHierarchy().getImplementersOf(clazz)) {
                                    if (Scene.v().getLibraryClasses().contains(imp))
                                        continue;
                                    String impName = imp.getName();
                                    bufferedWriter.write("  Implementers: " + impName);
                                    bufferedWriter.newLine();
                                }
                            }
                            else{ // if it is an class
                                // Get all super classes
                                for (SootClass superclass : Scene.v().getActiveHierarchy().getSuperclassesOf(clazz)) {
                                    if (Scene.v().getLibraryClasses().contains(superclass) || isJavaLibClass(superclass))
                                        continue;
                                    String superClassName = superclass.getName();
                                    bufferedWriter.write("  Superclasses: " + superClassName);
                                    bufferedWriter.newLine();
                                }
                                // Get all sub classes
                                for (SootClass subclass : Scene.v().getActiveHierarchy().getSubclassesOf(clazz)) {
                                    String subClassName = subclass.getName();
                                    bufferedWriter.write("  Subclasses: " + subClassName);
                                    bufferedWriter.newLine();
                                }
                                // Get all implements
                                for (SootClass inter : clazz.getInterfaces()) {
                                    if (Scene.v().getLibraryClasses().contains(inter) || isJavaLibClass(inter))
                                        continue;
                                    String interFaceName = inter.getName();
                                    bufferedWriter.write("  Implements: " + interFaceName);
                                    bufferedWriter.newLine();
                                }
                            }
                        }catch (Exception e) {
                            e.printStackTrace();
                        }
                    }
                    bufferedWriter.close();
                    fileWriter.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }));

        PackManager.v().runPacks();
        //PackManager.v().writeOutput();
    }

    public static boolean isJavaLibClass(SootClass sootClass){
        String name = sootClass.getName();
        if(name.startsWith("java")) 
            return true;
        if(name.startsWith("javax")) 
            return true;
        if(name.startsWith("sun")) 
            return true;
        return false;
    }  
}