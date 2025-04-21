// Build Traditional Call Graph

package com.example.hello;

import java.io.File;
import java.util.*;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.io.FileWriter;
import java.util.Iterator;

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
import java.io.BufferedWriter;

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

public class BuildAllCGRelease {

    public static void main(String[] args) {

        String inputFilePath = args[0];
        String outputFilePathRoot = args[1];
        String output_file_name = args[2];
        String outputFilePath;
        if(args.length >= 4){
            outputFilePath = outputFilePathRoot + output_file_name;
        }
        else{
            outputFilePath = outputFilePathRoot + output_file_name + "-PkgInfo-sootcg.txt";
        }

        String[] sootArgs = {
            "-pp",
            "-process-dir", inputFilePath,
            "-allow-phantom-refs",
            "-no-bodies-for-excluded", 
            "-whole-program",
            "-w",
            "-p", "cg.cha", "enabled:true", // use CHA algorithm
            "-dynamic-dir", inputFilePath,
        };
        Options.v().parse(sootArgs);
        Scene.v().loadNecessaryClasses();
        Options.v().setPhaseOption("cg", "all-reachable:true");
        Options.v().set_debug(true);

        PackManager.v().getPack("wjtp").add(new Transform("wjtp.myTransform", new SceneTransformer() {
            @Override
            protected void internalTransform(String phaseName, Map<String, String> options) {

                // Use SOOT to directly get CG
                System.out.println("prepare to get CG");
                CallGraph callgraph = Scene.v().getCallGraph();
                System.out.println("get CG success");

                // Output the call graph in batches
                Iterator<MethodOrMethodContext> source_iterator = callgraph.sourceMethods();
                int count = 0;
                int index = 0;
                BufferedWriter writer;
                StringBuilder stringBuilder = new StringBuilder();
                int divide_border = 1000; // batch size
                
                try{
                    writer = new BufferedWriter(new FileWriter(outputFilePath));
                    while(source_iterator.hasNext()){
                        count += 1;
                        MethodOrMethodContext this_source_method = source_iterator.next();
                        for (Iterator<Edge> it = callgraph.edgesOutOf(this_source_method); it.hasNext(); ) {
                            try {
                                Edge edge = it.next();
                                stringBuilder.append(edge.toString());
                                stringBuilder.append("\n");
                            } catch (Exception e) {
                                e.printStackTrace();
                            }
                        }
                        if(count!=0 && count % divide_border==0){
                            try {
                                index = count / divide_border;
                                System.out.println("output batch " + index);
                                String outputString = stringBuilder.toString();
                                writer.write(outputString);
                                stringBuilder.delete(0, stringBuilder.length());  
                            } catch (Exception e) {
                                e.printStackTrace();
                                return;
                            }
                        }
                    }
                    if(count % divide_border > 0){
                        try {
                            System.out.println("output final batch");
                            String outputString = stringBuilder.toString();
                            writer.write(outputString);
                            stringBuilder.delete(0, stringBuilder.length());  
                        } catch (Exception e) {
                            e.printStackTrace();
                            return;
                        }
                    }
                    writer.close();
                    System.out.println("output done");
                } catch (Exception ee) {
                    ee.printStackTrace();
                    return;
                }
            }
        }));

        PackManager.v().runPacks();
        //PackManager.v().writeOutput();

    }
}