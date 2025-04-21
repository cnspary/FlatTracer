# FlatTracer

This is a basic implementation of FlatTracer that shows how FlatTracer is working.

Environment: Linux system, python >= 3.7, Java >= 1.8

We provide two version of FlatTracer. Version 1 is the 'safer' versi. You can run it with FlatTracerMain.py. And Version 2 is the 'fast' version which consumes much more resources. You can run it with FlatTracerMainFast.py.

### Step 1: Install requirements

`pip install networkx`

### Step 2: Compile Java code

`javac -cp path_to_Dependency/soot-4.4.1-jar-with-dependencies.jar:path_to_Dependency/fastjson-1.2.83.jar  path_to_this_dir/com/example/hello/*.java`

### Step 3: Set up input file

You can directly use examples in ./InputExamples, or use your own input data to replace it.

### Step 4: Run FlatTracer

`python3 FlatTracerMain.py ./InputExamples/InputExample_1.json`

or

`python3 FlatTracerMainFast.py ./InputExamples/InputExample_1.json`

When recovering the traditional path in each package, FlatTracer by default only finds the function call path whose length is equal to the shortest path. If you want to expand the search to a longer path, you can modify myVariable.path_additional_len

FlatTracer uses CHA algorithm by default. If you want to enable SPARK(Points-to Analysis), you can modify myVariable.enable_sprak. However, the CHA algorithm is a more suitable choice for our special process of generating CG of each package separately and stitching them later.
