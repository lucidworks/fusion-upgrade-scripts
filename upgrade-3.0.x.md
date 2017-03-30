## Upgrade to any Fusion version 3.0.x from version 3.0.0 or above

These scripts require that the following Python libraries are already installed: kazoo

Steps to upgrade Fusion (for example from version 3.0.0 to 3.0.1)

1. Download new version of Fusion
2. Extract it to the same parent fusion folder as for ver 3.0.0. (For example, if the fusion 3.0.0 is installed in
   /opt/fusion/3.0.0 folder, place the downloaded fusion-3.0.1.tar.gz file to /opt/ folder and run command:

   ```
    tar zxvf fusion-3.0.1.tar.gz
    ```

3. Set FUSION_OLD_HOME env variable to be the full path of the old version of Fusion (3.0.0) folder:

    `export FUSION_OLD_HOME=/path/to/fusion/3.0.0`

4. Set FUSION_HOME env variable to be the full path of the new version of Fusion (3.0.1) folder:

    `export FUSION_HOME=/path/to/fusion/3.0.1`

5. Copy data from older fusion instance to new fusion instance

   `cp -R $FUSION_OLD_HOME/data/  $FUSION_HOME/`

6. Copy configs from older fusion instance to new fusion instance:

    ```
    mv $FUSION_HOME/conf/ $FUSION_HOME/conf_backup/
    cp -R $FUSION_OLD_HOME/conf/  $FUSION_HOME/
    ```

    If you are running distributed fusion, this step would have to be performed on all the Fusion nodes.

   ---
   
   **NOTE**: If you are running external Solr or Zookeeper, then modify the `group.default` property in
    fusion.properties to reflect the services that should be started when `bin/fusion` script is executed. 
   
   ---

7. Update links to point to new fusion instance

    ```
    cd $FUSION_HOME/..
    unlink latest
    ln -s 3.0.1 latest
    ```

8. Start the Zookeeper server which will be used by the new Fusion installation. If you are using the Zookeeper bundled within Fusion, that would be:

    ```
    cd $FUSION_HOME
    ./bin/zookeeper start
    ```

9. Run the upgrade script

    ```
    cd fusion-upgrade-scripts/src
    python upgrade-3.0.x.py
    ```

10. Run 3.0.1 fusion (all services defined in fusion.properties) and validate via Fusion UI
    ```
    cd $FUSION_HOME
    ./bin/fusion start
    ```

11. Before accessing the Fusion UI, make sure to clear your browser's cache. Otherwise, you may inadvertently access a cached version of the old Fusion UI and see inconsistent behavior.

