function Get-param_operation{
   Param ($userinput,$output_path)
   # Split user input provided to get build version detail
   $delimiter = "rb_my"

   $array_val = $userinput -split $delimiter
   $build_version = $delimiter+$array_val[1]

   $delimiter_2 = "-"
   $addr = $build_version -split $delimiter_2

   # Check which repository does the variant is available
   if(($addr[3]) -like "ONREVIEW*"){
      $repo_name = "gmvcu-shadow-repos"
   }
   elseif(-not ($addr[2])){
      $repo_name = "gmvcu-repos"
   }
   else{
      $repo_name = "gmvcu-shadow-repos"
   }
   # Call download function
   myfunc_download_artifact $build_version $userinput $repo_name $output_path
}


function myfunc_download_artifact{
   Param ($build_version,$userinput,$repo_name,$output_path)

   Write-Host "`n"
   write-host "Build version provided   :"$build_version
   Write-Host "Variant option provided  :"$userinput
   write-host "Repository to download   :"$repo_name
   write-host "Download path provided   :"$output_path
   Write-Host "`n"

   # Creating artifact_downloads folder in specified output path
   if (!(Test-Path -Path $output_path)) {
      New-Item -itemType Directory -Path $output_path -Name "artifact_downloads" | Out-Null
   }else{
      New-Item -ItemType Directory -Force -Path $output_path\artifact_downloads | Out-Null
   }

   if(($userinput) -like "AUTOSAR*"){
      $repo_path = "autosar"
   }else{
      $repo_path = "multi"
   }

   # Download single artifact from artifactory
   perl download_single_artifact.pl -mode fast -r ${repo_name} -o ${output_path}/artifact_downloads/${repo_path}/${userinput} -c bosch/deployment/${build_version}/${repo_path}/${userinput}.tar.gz

   if($LASTEXITCODE -ne 0){
      Write-Host "`n"
      Write-Host "Download Failed!"
   }else{
      Write-Host "`n"
      Write-Host "Download successful or already existed!"
      Write-Host "`n"
      Write-Host "Binary will be available in the path: ${output_path}\artifact_downloads\${repo_path}\${userinput}"
      Write-Host "`n"
   }

}

function get-user_input{
   Write-Host "`n"
   Write-Host "Important! Artifactory download is case sensitive. Please provide exact values."
   Write-Host "`n"
   Write-Host "Domain Build ID name  [Examples]"

   Write-Host "For On-Review like - AUTOSAR-CLEA-USER-rb_my23_main_2021.26.4-4-g8dc7b4d59-ONREVIEW_309211_16"
   Write-Host "For Hourly like    - AUTOSAR-CLEA-USER-rb_my23_main_2021.26.4-6-gdf9978993"
   Write-Host "For Daily like     - AUTOSAR-CLEA-USER-rb_my23_main_2021.26.4"
   Write-Host "`n"
   $var0 = Read-Host -Prompt 'Please provide the Domain Build ID'
   Write-Host "`n"
   $var1 = Read-Host -Prompt 'Please provide the output path to download'

   # Call get parameters function
   Get-param_operation $var0 $var1
}

# If less than 1 command line arguments passed will run through if loop
if(($args.Count) -eq 2){
   $var0 = $args[0]
   $var1 = $args[1]
   Get-param_operation $var0 $var1
}else{
   get-user_input
}