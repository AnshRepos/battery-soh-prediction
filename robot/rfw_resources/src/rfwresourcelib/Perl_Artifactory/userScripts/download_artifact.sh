#!/bin/bash
myfunc_download_artifact()
{
    echo
    echo "Build version provided   : $1"
    echo "Variant option provided  : $2"
    echo "Repository to download   : $3"
    echo "Download path provided   : $4"
    echo

    # Creating artifact_downloads folder in the specified output directory
    if [ ! -d "$4/artifact_downloads" ] ; then
        mkdir $4/artifact_downloads
    fi

    if [[ ${2} == "AUTOSAR"* ]]; then
        export repo_path="autosar"
    else
        export repo_path="multi"
    fi

    perl download_single_artifact.pl -mode fast -r ${3} -o $4/artifact_downloads/${repo_path}/${2} -c bosch/deployment/${1}/${repo_path}/${2}.tar.gz

    if [ $? -eq 0 ]; then
        echo
        echo "Download successful or already existed!"
        echo
        echo "Binary will be available in the path : $4/artifact_downloads/${repo_path}/${2}"
        echo
    else
        echo "Download failed!"
    fi
}

myfunc_parameters()
{
    export variant=${1%%*( )}  # check whether the input provided by user have space at the end and remove it
    export output_path=${2%%*()}

    # split user input provided to get build version detail
    delimiter=rb_my  # splitting string using the delimiter "rb_my23" to retrieve build version separately
    user_input=$variant$delimiter
    array=();
    while [[ $user_input ]]; do
        array+=( "${user_input%%"$delimiter"*}" );
        user_input=${user_input#*"$delimiter"};
    done;

    build_version=${delimiter}${array[1]}

    # check which repository does the variant is available
    IFS='-' read -ra ADDR <<< "$build_version"

    if [[ ${ADDR[3]} == *"ONREVIEW"* ]]; then
        export repo_name="gmvcu-shadow-repos"
    elif [ -z "${ADDR[2]}" ] ; then
        export repo_name="gmvcu-repos"
    else
        export repo_name="gmvcu-shadow-repos"
    fi

    # Call download function
    myfunc_download_artifact $build_version $variant $repo_name $output_path
}

# If less than 1 command line arguments passed will run through if loop
if [ "$#" -lt 2 ]; then
    echo
    echo "Important! Artifactory download is case sensitive. Please provide exact values."
    echo
    read -p "Please provide the Domain Build ID name  [Examples]

For On-Review like - AUTOSAR-CLEA-USER-rb_my23_main_2021.26.4-4-g8dc7b4d59-ONREVIEW_309211_16
For Hourly like    - AUTOSAR-CLEA-USER-rb_my23_main_2021.26.4-6-gdf9978993
For Daily like     - AUTOSAR-CLEA-USER-rb_my23_main_2021.26.4

Please provide the Domain Build ID:"  var0
    echo
    read -p "Please provide the output path to download:" var1
    echo
    # call parameters function
    myfunc_parameters $var0 $var1
else
    var0=$1;
    var1=$2;
    # call parameters function
    myfunc_parameters $var0 $var1

fi