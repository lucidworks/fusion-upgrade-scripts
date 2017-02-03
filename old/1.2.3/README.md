**Upgrade notes for upgrading from 1.2.0, 1.2.1 to 1.2.3**.

Pre-requisites
--------------

1. Install Python 2.7.2+ and Kazoo library (https://kazoo.readthedocs.org/en/latest/install.html)
2. Make sure there is enough free disk space (more than what current fusion directory occupies)
3. `cd` to the base directory of an existing Fusion install. (E.g, if `fusion` is installed at `/opt/lucidworks/fusion`, then do `cd /opt/lucidworks`).
4. All the below commands assume the user is in the base directory of an existing Fusion install. Copy the latest version of fusion to the base directory.
5. Download the upgrade scripts from the Git repo

    ```
    curl -L -o fusion-upgrade-scripts.tar.gz http://github.com/Lucidworks/fusion-upgrade-scripts/tarball/1.2.3/
    mkdir -p fusion-upgrade-scripts
    tar -C fusion-upgrade-scripts --strip-components=1 -xf fusion-upgrade-scripts.tar.gz
    ```

Steps to Upgrade
----------------

1. Ensure that no administrators are making changes to Fusion config. Querying may continue.
2. Install the new version in a folder next to the old version

    ```
      mkdir -p fusion-new
      tar -C fusion-new --strip-components=1 -xf fusion-1.2.3.tar.gz (Substitute fusion-1.2.3.tar.gz with the actual tar file of new Fusion install)
    ```
3. Stop all services of Fusion except ZK

   ```
      fusion/bin/ui stop
      fusion/bin/connectors stop
      fusion/bin/api stop
   ```

4. cd to the upgrade scripts directory

    ```
       cd fusion-upgrade-scripts
    ```

5. Run the export script against the running zookeeper (You need to run this script only once if you have multiple Fusion instances)

    ```
      python zk_export.py {zk_address} {output_filename}
      E.g., python zk_export.py localhost:9983 zk_fusion.export
    ```

6. Run the update script against the exported file  (You need to run this script only once if you have multiple Fusion instances)

    ```
       python convert_zk_data.py {exported file from previous command} {introspect file shipped with scripts} {new file to save updates}
       E.g., python convert_zk_data.py zk_fusion.export introspect.json zk_fusion_updated.export
    ```

7. Change back to the base directory

    ```
       cd ..
    ```

8. Copy any changes (after old installation) from `fusion/bin/config.sh` to the new config `fusion-new/bin/config.sh`. Be careful and do **NOT** copy the file `config.sh` from old to new, since the new config file might have been updated. If you haven't changed anything in your `config.sh`, then there is no need to make any changes to the new instance `config.sh`. Also, check your bin scripts for any changes and substitute them in config.sh
    * E.g., 1.2.0 has 'JAVA_OPTIONS' setting defined in each individual bash scripts `fusion/bin/solr`, `fusion/bin/connectors`, `fusion/bin/api`, `fusion/bin/ui`. In 1.2.3, we have moved the JAVA_OPTIONS from bin scripts to config.sh. You will see `API_JAVA_OPTIONS`, `CONNECTORS_JAVA_OPTIONS`, `SOLR_JAVA_OPTIONS`, `UI_JAVA_OPTIONS` in `fusion-new/bin/config.sh`. So, if you have made any changes to the `JAVA_OPTIONS` in individual bin scripts, please update the related config in `fusion-new/bin/config.sh`

9. Copy crawldb from old to new Fusion

  ```
      cp -R fusion/data/connectors/crawldb fusion-new/data/connectors/
  ```

10. Copy uploaded JDBC drivers

  ```
     cp -R fusion/data/connectors/lucid.jdbc fusion-new/data/connectors/
  ```

11. Please follow the different deployment scenarios below
  
   a. If you are using the Fusion-embedded Solr and Zookeeper (Out of the box Fusion):
      * Stop the Solr service if not already stopped
    
        `fusion/bin/solr stop`
      * Copy ZK configuration data to the new installation
    
        `cp -R fusion/solr/zoo* fusion-new/solr/`
      * move Solr collection data to the new installation: (This might take a while depending on the amount of data in Solr)

          ```
              find fusion/solr -maxdepth 1 -mindepth 1 | grep -v -E "zoo*" | while read f ; do cp -R  $f fusion-new/solr/; done
          ```

   b. If you are using external Zookeeper and using the Solr inside `fusion` directory:
      * Stop the Solr service if not already stopped `fusion/bin/solr stop`
      * move Solr collection data to the new installation:
      
          ```
              find fusion/solr -maxdepth 1 -mindepth 1 | grep -v -E "zoo*" | while read f ; do cp -R  $f fusion-new/solr/; done
          ```

   c. If you are using external Zookeeper and external Solr. (not using Solr, ZK in the fusion directory):
      * No need to do anything. Proceed to the next step

12. If you are using embedded ZK, start ZK from new Fusion instance. After starting, wait for Solr to show up in the Admin UI at port 8983 (http://localhost:8983/solr)
    Don't run this if you are not using the embedded ZK inside fusion package

    ```
       fusion-new/bin/solr start
    ```

13. Change to upgrade scripts directory and run the script to update data inside ZK  (You need to run this script only once if you have multiple Fusion instances)

    ```
      cd fusion-upgrade-scripts
      python update_zk_data.py {zk_host} {updated_exported_file_name}
      E.g., python update_zk_data.py localhost:9983 zk_fusion_updated.export
    ```

14. Change back to the base directory

    ```
    cd ..
    ```

15. Start the fusion services in the new instance. (Start each service individually and check the individual logs to make sure there are no errors)
  
  a. If you are using Solr inside Fusion package and embedded Zookeeper within the Solr (Out of the box Fusion):

    ```
     fusion-new/bin/api start
     fusion-new/bin/connectors start
     fusion-new/bin/ui start
    ```

  b. If you are using Solr inside Fusion but not the embedded ZK inside Solr, then comment out `-DzkRun` inside the bin scripts `fusion-new/bin/solr` 

   ```
    fusion-new/bin/solr start
    fusion-new/bin/api start
    fusion-new/bin/connectors start
    fusion-new/bin/ui start
   ```

  c. If you are not using Solr inside the Fusion package, then use the below commands to run the other services

   ```
     fusion-new/bin/api start
     fusion-new/bin/connectors start
     fusion-new/bin/ui start
   ```

16. Once Admin UI boots up, Log in and ensure that your stuff looks good at this point. Few examples: Check

    1.   If you can access all the collections
    2.  If all the permissions for roles are displayed in the UI
    3. If you can search data inside collections
    4.  Access datasources, etc..

17. Stop the new Fusion:

      ```
      fusion-new/bin/fusion stop
      ```

18. Rename the directories:

      ```
      mv fusion fusion-old
      mv fusion-new fusion
      ```

19. Startup Fusion: (Note: If you are not running Solr inside fusion, then comment out the solr script invocations in `fusion/bin/fusion`)

     ```
     fusion/bin/fusion start
     ```

Optional
--------

#### After successful upgrade

* If you are certain your upgrade was successful, you can delete or archive the old version by deleting or archiving fusion-old


#### Rollback to Old version

   * If you want to roll back to old version :

     ```
      fusion/bin/fusion stop
      mv fusion fusion-new-rolledback
      mv fusion-old fusion
     ```

Notes
-----

* Clear your browser cache after starting Admin UI in the new Fusion instance
* Warning message below is expected while running the script to convert permissions
    `2015-06-08 18:54:06,196 - convert_permission - WARNING - 153 - Could not find service name 'hosts' in the introspect`
* There was a bug in 1.2.1, 1.2.0 that prevented system metrics from being aggregated (in collection system_metrics).
  After upgrading to 1.2.3, the old system metrics will not be aggregated.
