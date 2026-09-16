using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;

namespace PPgCompiler
{
    class Program
    {
        static void Main(string[] args)
        {
            // Usage: ++g yourfile.ppc
            if (args.Length != 1)
            {
                Console.Error.WriteLine("++g — ++Ↄ to C++ Compiler");
                Console.Error.WriteLine("Usage: ++g yourfile.ppc");
                Environment.Exit(1);
            }

            string inputFile = args[0];

            if (!File.Exists(inputFile))
            {
                Console.Error.WriteLine($"Error: File '{inputFile}' not found!");
                Environment.Exit(2);
            }

            try
            {
                // Step 1: Read source
                string ppcSource = File.ReadAllText(inputFile);

                // Step 2: Preprocess — split by whitespace, reverse order
                string cppCode = Preprocess(ppcSource);

                // Optional: Show generated code for debugging
                // Console.Error.WriteLine("--- Generated C++ ---");
                // Console.Error.WriteLine(cppCode);
                // Console.Error.WriteLine("--- End ---");

                // Step 3: Compile & Run
                string exePath = CompileAndRun(cppCode, inputFile);

                // Cleanup
                if (File.Exists(exePath))
                    File.Delete(exePath);
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Error: {ex.Message}");
                Environment.Exit(3);
            }
        }

        // ++Ↄ Preprocessor: split by whitespace → reverse token order
        static string Preprocess(string source)
        {
            // Split on whitespace (spaces, tabs, newlines)
            string[] tokens = source.Split(
                new char[] {' ', '\t', '\n', '\r'},
                StringSplitOptions.RemoveEmptyEntries
            );

            // Reverse and join with newlines
            Stack<string> stack = new Stack<string>(tokens);
            StringBuilder result = new StringBuilder();
            while (stack.Count > 0)
            {
                result.AppendLine(stack.Pop());
            }

            return result.ToString();
        }

        static string CompileAndRun(string cppCode, string inputFile)
        {
            // Generate temp filenames
            string baseName = Path.GetFileNameWithoutExtension(inputFile);
            string tempCpp = Path.Combine(Path.GetTempPath(), $"{baseName}_{Guid.NewGuid():N}.cpp");
            string tempExe = Path.Combine(Path.GetTempPath(), $"{baseName}_{Guid.NewGuid():N}");

            try
            {
                // Write .cpp file
                File.WriteAllText(tempCpp, cppCode);

                // Step A: Compile with g++
                ProcessStartInfo compileInfo = new ProcessStartInfo
                {
                    FileName = "g++",
                    Arguments = $"\"{tempCpp}\" -o \"{tempExe}\" -std=c++17",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false
                };

                using (Process compile = Process.Start(compileInfo))
                {
                    string compileOut = compile.StandardOutput.ReadToEnd();
                    string compileErr = compile.StandardError.ReadToEnd();
                    compile.WaitForExit();

                    if (compile.ExitCode != 0)
                    {
                        Console.Error.WriteLine("Compilation failed:");
                        if (!string.IsNullOrWhiteSpace(compileErr))
                            Console.Error.WriteLine(compileErr);
                        if (!string.IsNullOrWhiteSpace(compileOut))
                            Console.Error.WriteLine(compileOut);
                        throw new Exception($"g++ exited with code {compile.ExitCode}");
                    }
                }

                // Step B: Run the compiled program
                ProcessStartInfo runInfo = new ProcessStartInfo
                {
                    FileName = tempExe,
                    RedirectStandardOutput = false,
                    RedirectStandardError = false,
                    UseShellExecute = false
                };

                using (Process run = Process.Start(runInfo))
                {
                    run.WaitForExit();
                }

                return tempExe;
            }
            finally
            {
                // Always clean up .cpp temp file
                if (File.Exists(tempCpp))
                    File.Delete(tempCpp);
            }
        }
    }
}
