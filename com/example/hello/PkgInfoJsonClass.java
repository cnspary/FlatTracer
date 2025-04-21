package com.example.hello;

import java.util.*;
import java.util.Iterator;
import java.util.Map;
import java.io.File;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.annotation.JSONField;
import com.alibaba.fastjson.annotation.JSONType;

@JSONType(orders = {"GAV",  
                    "PackageName",
                    "AllFunctionDict",
                    "DynamicInvokeFunctions",
                    "InstanceInvokeFunctions",
                    "InterfaceInvokeFunctions",
                    "SpecialInvokeFunctions",
                    "StaticInvokeFunctions",
                    "VirtualInvokeFunctions",
                    "CrossPackageFunctions",
                    "EntranceAndReachableFunctions"})
public class PkgInfoJsonClass {

    @JSONField(name = "GAV")
    private String GAV;
    @JSONField(name = "PackageName")
    private List<String> PackageName;
    @JSONField(name = "AllFunctionDict")
    private Map<String, String> AllFunctionDict;
    @JSONField(name = "DynamicInvokeFunctions")
    private Set<String> DynamicInvokeFunctions;
    @JSONField(name = "InstanceInvokeFunctions")
    private Set<String> InstanceInvokeFunctions;
    @JSONField(name = "InterfaceInvokeFunctions")
    private Set<String> InterfaceInvokeFunctions;
    @JSONField(name = "SpecialInvokeFunctions")
    private Set<String> SpecialInvokeFunctions;
    @JSONField(name = "StaticInvokeFunctions")
    private Set<String> StaticInvokeFunctions;
    @JSONField(name = "VirtualInvokeFunctions")
    private Set<String> VirtualInvokeFunctions;
    @JSONField(name = "CrossPackageFunctions")
    private Set<String> CrossPackageFunctions;
    @JSONField(name = "EntranceAndReachableFunctions")
    private Map<String, Set<String>> EntranceAndReachableFunctions;

    public String getGAV() {
        return GAV;
    }

    public void setGAV(String GAV) {
        this.GAV = GAV;
    }

    public List<String> getPackageName() {
        return PackageName;
    }

    public void setPackageName(List<String> packageName) {
        PackageName = packageName;
    }

    public Map<String, String> getAllFunctionDict() {  
        return AllFunctionDict;  
    }  
  
    public void setAllFunctionDict(Map<String, String> allFunctionDict) {  
        this.AllFunctionDict = allFunctionDict;  
    }  
  
    public Set<String> getDynamicInvokeFunctions() {  
        return DynamicInvokeFunctions;  
    }  
  
    public void setDynamicInvokeFunctions(Set<String> dynamicInvokeFunctions) {  
        this.DynamicInvokeFunctions = dynamicInvokeFunctions;  
    }  
  
    public Set<String> getInstanceInvokeFunctions() {  
        return InstanceInvokeFunctions;  
    }  
  
    public void setInstanceInvokeFunctions(Set<String> instanceInvokeFunctions) {  
        this.InstanceInvokeFunctions = instanceInvokeFunctions;  
    }  
   
    public Set<String> getInterfaceInvokeFunctions() {  
        return InterfaceInvokeFunctions;  
    }  
  
    public void setInterfaceInvokeFunctions(Set<String> interfaceInvokeFunctions) {  
        this.InterfaceInvokeFunctions = interfaceInvokeFunctions;  
    }  
  
    public Set<String> getSpecialInvokeFunctions() {  
        return SpecialInvokeFunctions;  
    }  
  
    public void setSpecialInvokeFunctions(Set<String> specialInvokeFunctions) {  
        this.SpecialInvokeFunctions = specialInvokeFunctions;  
    }  
  
    public Set<String> getStaticInvokeFunctions() {  
        return StaticInvokeFunctions;  
    }  
  
    public void setStaticInvokeFunctions(Set<String> staticInvokeFunctions) {  
        this.StaticInvokeFunctions = staticInvokeFunctions;  
    }  
  
    public Set<String> getVirtualInvokeFunctions() {  
        return VirtualInvokeFunctions;  
    }  
  
    public void setVirtualInvokeFunctions(Set<String> virtualInvokeFunctions) {  
        this.VirtualInvokeFunctions = virtualInvokeFunctions;  
    }  
  
    public Set<String> getCrossPackageFunctions() {  
        return CrossPackageFunctions;  
    }  
  
    public void setCrossPackageFunctions(Set<String> crossPackageFunctions) {  
        this.CrossPackageFunctions = crossPackageFunctions;  
    }  

    public Map<String, Set<String>> getEntranceAndReachableFunctions() {  
        return EntranceAndReachableFunctions;  
    }  
  
    public void setEntranceAndReachableFunctions(Map<String, Set<String>> entranceAndReachableFunctions) {  
        this.EntranceAndReachableFunctions = entranceAndReachableFunctions;  
    }  
}
